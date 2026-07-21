#!/usr/bin/env bash
#
# setup_vllm_xpu.sh — Serve LLMs on Intel GPUs (XPU) with vLLM for Haystack.
#
# Referenced by the Intel-GPU cookbook notebooks:
#   - notebooks/intel_gpu_rag.ipynb          (served RAG with vLLM)
#   - notebooks/vllm_inference_engine.ipynb  (Intel GPU section)
#
# Starts an OpenAI-compatible vLLM server on an Intel GPU. Haystack then talks
# to it with zero code changes via `api_base_url` / OPENAI_BASE_URL.
#
# Requirements:
#   - Intel Arc / Data Center GPU + drivers (compute-runtime >= 26.18 recommended)
#   - Docker with the current user able to run it
#
# Usage:
#   ./setup_vllm_xpu.sh                                   # chat model on GPU 0, port 8000
#   MODEL=... PORT=... ZE_AFFINITY_MASK=1 ./setup_vllm_xpu.sh
#   TASK=embed PORT=8001 ZE_AFFINITY_MASK=1 ./setup_vllm_xpu.sh   # embedding server
#
set -euo pipefail

IMAGE="${IMAGE:-intel/vllm:0.10.2-xpu}"
MODEL="${MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"
PORT="${PORT:-8000}"
GPU_MASK="${ZE_AFFINITY_MASK:-0}"          # "0" for one GPU, "0,1,2,3" for tensor-parallel
TP_SIZE="${TP_SIZE:-1}"
TASK="${TASK:-}"                            # set to "embed" for embedding models
MAX_LEN="${MAX_LEN:-4096}"
GPU_MEM="${GPU_MEM:-0.85}"
NAME="${NAME:-vllm-xpu-${PORT}}"
HF_CACHE="${HF_CACHE:-$HOME/.cache/huggingface}"

command -v docker >/dev/null || { echo "ERROR: docker not found." >&2; exit 1; }

# Proxy: containers do NOT inherit the host proxy. Pass it through if set,
# otherwise fall back to offline mode (requires the model to be pre-cached).
proxy_args=()
if [ -n "${http_proxy:-${HTTP_PROXY:-}}" ]; then
  P="${http_proxy:-${HTTP_PROXY}}"
  proxy_args+=(-e "http_proxy=${P}" -e "https_proxy=${P}" -e "no_proxy=localhost,127.0.0.1,0.0.0.0")
else
  echo "No host proxy set — using HF_HUB_OFFLINE=1 (model must be pre-cached in ${HF_CACHE})."
  proxy_args+=(-e "HF_HUB_OFFLINE=1" -e "TRANSFORMERS_OFFLINE=1")
fi

# Embedding models need --task embed; generation/ranking models don't.
task_args=()
[ "${TASK}" = "embed" ] && task_args+=(--task embed)

# Free a stale port held by a crashed --network=host container.
pid="$(ss -tlnp 2>/dev/null | grep ":${PORT} " | grep -oE 'pid=[0-9]+' | cut -d= -f2 | head -1 || true)"
[ -n "${pid}" ] && { echo "Freeing port ${PORT} (killing PID ${pid})"; kill "${pid}" 2>/dev/null || true; sleep 2; }
docker rm -f "${NAME}" 2>/dev/null || true

echo "Starting ${IMAGE}: model=${MODEL} port=${PORT} ZE_AFFINITY_MASK=${GPU_MASK} tp=${TP_SIZE} ${TASK:+task=${TASK}}"
# NOTE: the image entrypoint is the vLLM OpenAI API server, so pass vLLM args
# directly — NO `vllm serve` prefix and NO `--device` (XPU is auto-detected).
docker run -d --name "${NAME}" \
  --network=host \
  --device /dev/dri:/dev/dri \
  -v /dev/dri/by-path:/dev/dri/by-path \
  -v "${HF_CACHE}:/root/.cache/huggingface" \
  --ipc=host --shm-size=8g \
  "${proxy_args[@]}" \
  -e "ZE_AFFINITY_MASK=${GPU_MASK}" \
  "${IMAGE}" \
  --model "${MODEL}" \
  --dtype float16 --max-model-len "${MAX_LEN}" \
  --gpu-memory-utilization "${GPU_MEM}" \
  --tensor-parallel-size "${TP_SIZE}" \
  --enforce-eager \
  "${task_args[@]}" \
  --host 0.0.0.0 --port "${PORT}"

echo "Waiting for server on :${PORT} (model load can take a few minutes)..."
for i in $(seq 1 60); do
  if curl -s "http://localhost:${PORT}/v1/models" 2>/dev/null | grep -q '"data"'; then
    echo "Ready. Endpoint: http://localhost:${PORT}/v1"
    exit 0
  fi
  docker ps --format '{{.Names}}' | grep -q "^${NAME}$" || { echo "Container exited:"; docker logs "${NAME}" 2>&1 | tail -15; exit 1; }
  sleep 10
done
echo "Timed out. Check: docker logs ${NAME}"; exit 1
