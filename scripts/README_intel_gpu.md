# Serving models on Intel GPUs (XPU) for the Intel-GPU cookbooks

Setup guide for the Intel-GPU notebooks:
- [`notebooks/intel_gpu_rag.ipynb`](../notebooks/intel_gpu_rag.ipynb) — served RAG with vLLM
- [`notebooks/intel_gpu_inprocess_rag.ipynb`](../notebooks/intel_gpu_inprocess_rag.ipynb) — in-process (no server)
- [`notebooks/vllm_inference_engine.ipynb`](../notebooks/vllm_inference_engine.ipynb) — has an Intel GPU section

There are two ways to run models on Intel GPUs with Haystack.

---

## Option A — Served with vLLM (container)

Highest throughput; used by `intel_gpu_rag.ipynb` and the vLLM notebook. Uses
Intel's official vLLM image ([Docker Hub](https://hub.docker.com/r/intel/vllm)),
which bundles the oneAPI runtime + PyTorch XPU build + vLLM XPU kernels.

**Requirements:** Intel Arc / Data Center GPU, drivers (compute-runtime ≥ 26.18
recommended), Docker.

Use the helper script in this folder:

```bash
# Generation model on GPU 0, port 8000
./scripts/setup_vllm_xpu.sh

# Embedding model on GPU 1, port 8001 (embedding models need TASK=embed)
MODEL=sentence-transformers/all-MiniLM-L6-v2 TASK=embed \
  PORT=8001 ZE_AFFINITY_MASK=1 GPU_MEM=0.3 ./scripts/setup_vllm_xpu.sh

# Ranking model on GPU 2, port 8002
MODEL=BAAI/bge-reranker-base \
  PORT=8002 ZE_AFFINITY_MASK=2 GPU_MEM=0.3 ./scripts/setup_vllm_xpu.sh
```

Then, from Haystack (no code changes — vLLM is OpenAI-compatible):

```python
from haystack_integrations.components.generators.vllm import VLLMChatGenerator
llm = VLLMChatGenerator(model="Qwen/Qwen2.5-1.5B-Instruct",
                        api_base_url="http://localhost:8000/v1")
```

### Key Intel-specific points (and gotchas)

| Point | Why |
|-------|-----|
| `--device /dev/dri` + `-v /dev/dri/by-path` | Passes Intel GPU render devices into the container. |
| `ZE_AFFINITY_MASK=0` | Selects which GPU(s). **Set it** — without it, multi-GPU enumeration can stall at startup. Use `0,1,2,3` + `TP_SIZE=4` to shard across 4 GPUs. |
| No `--device xpu`, no `vllm serve` prefix | The image entrypoint *is* the API server; XPU is auto-detected. Pass vLLM args directly. |
| Proxy passthrough | Containers don't inherit the host proxy. The script forwards `http_proxy`/`https_proxy` if set; otherwise it uses `HF_HUB_OFFLINE=1` (model must be pre-cached). |
| `--task embed` for embedding models | Without it the `/v1/embeddings` route isn't registered. The script adds it when `TASK=embed`. |
| Port already in use | A crashed `--network=host` container can hold the port. The script frees it automatically. |

Manage containers: `docker logs -f vllm-xpu-8000` · `docker rm -f vllm-xpu-8000`

### Native / source build (no Docker)

There are no pre-built vLLM XPU wheels on PyPI; build from source:
see the [vLLM XPU installation docs](https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html?device=xpu).
Remember to replace the NVIDIA `triton` with `triton-xpu` after installing.

---

## Option B — In-process (no server)

Simplest path; used by `intel_gpu_inprocess_rag.ipynb`. Models load directly into
the Python process via PyTorch's XPU backend — no Docker, no server.

```bash
# The only hardware-specific install — bundles the Intel oneAPI runtime:
pip install torch --index-url https://download.pytorch.org/whl/xpu
pip install haystack-ai "transformers[sentencepiece]" "sentence-transformers>=5.0.0" accelerate
```

Verify the GPU is visible:

```bash
python -c "import torch; print(torch.xpu.is_available(), torch.xpu.device_count())"
```

Haystack auto-selects the XPU (device precedence CUDA > XPU > MPS > CPU), so
`SentenceTransformersTextEmbedder`, `HuggingFaceLocalChatGenerator`, etc. run on
the Intel GPU with no extra config. Pin a specific GPU with
`device=ComponentDevice.from_str("xpu:0")`.

---

## Which should I use?

- **In-process (B):** development, single-user, embedding/reranking. Simplest.
- **Served with vLLM (A):** production, concurrent requests, multi-GPU sharding, higher throughput.
