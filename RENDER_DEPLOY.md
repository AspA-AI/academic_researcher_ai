# Deploy AI Researcher to Render

Step-by-step guide to deploy the AI Researcher app on [Render](https://render.com).

---

## Prerequisites

- [ ] **GitHub account** – Render deploys from Git
- [ ] **Code in a Git repo** – Push `ai_researcher` to GitHub (as its own repo or in a monorepo)
- [ ] **OpenAI API key** – [platform.openai.com](https://platform.openai.com) → API keys
- [ ] **Weaviate instance** – See [Weaviate setup](#weaviate-setup) below

---

## 1. Push Your Code to GitHub

If `ai_researcher` is not yet in a repo:

```bash
cd ai_researcher
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/ai-researcher.git
git push -u origin main
```

If it’s inside a monorepo (e.g. `A{sp}A`), push the whole repo and use the **Root Directory** setting in step 4.

---

## 2. Create a Render Account

1. Go to [render.com](https://render.com)
2. Click **Get Started**
3. Sign up with GitHub

---

## 3. Create a New Web Service

1. In the [Render Dashboard](https://dashboard.render.com), click **New +** → **Web Service**
2. Connect your GitHub account if needed
3. Select the repo that contains `ai_researcher`:
   - If the repo root is `ai_researcher`: select that repo
   - If it’s a monorepo: select the repo and set **Root Directory** to `ai_researcher` in the next step

---

## 4. Configure the Service

| Field | Value |
|-------|-------|
| **Name** | `ai-researcher` (or any name) |
| **Region** | Oregon (US West) or nearest |
| **Root Directory** | `ai_researcher` (if inside a monorepo; otherwise leave blank) |
| **Runtime** | **Docker** |
| **Dockerfile Path** | `Dockerfile` (or `ai_researcher/Dockerfile` if Root Directory is parent) |
| **Instance Type** | **Free** (try first; upgrade to Starter if you hit OOM) |

---

## 5. Add Environment Variables

In **Environment** → **Add Environment Variable**:

| Key | Value | Secret? |
|-----|-------|--------|
| `OPENAI_API_KEY` | `sk-...` | Yes |
| `WEAVIATE_URL` | `https://your-cluster.weaviate.network` | No |
| `WEAVIATE_API_KEY` | Your Weaviate API key (if required) | Yes |
| `SERVE_CLIENT` | `true` | No |
| `DISABLE_RERANKER` | `true` | **Required on Free tier** – avoids OOM (512MB limit). Skips cross-encoder reranking; retrieval still works. |

To add secrets:
1. Open **Environment**
2. Click **Add Environment Variable**
3. Set **Key** and **Value**
4. Turn **Secret** on for `OPENAI_API_KEY` and `WEAVIATE_API_KEY`

---

## 6. Deploy

1. Click **Create Web Service**
2. Render will build and deploy
3. First build can take 10–15 minutes (sentence-transformers install)
4. Final URL: `https://ai-researcher-xxxx.onrender.com`

---

## Weaviate Setup

The app needs a Weaviate instance for document retrieval.

### Option A: Weaviate Cloud (recommended)

1. Go to [weaviate.io](https://weaviate.io) → **Get Started**
2. Create a sandbox cluster (14-day free trial)
3. Copy the cluster URL and API key
4. Set `WEAVIATE_URL` and `WEAVIATE_API_KEY` in Render

### Option B: Self-hosted

If you already run Weaviate (e.g. Docker locally or another cloud), use that URL:

- `WEAVIATE_URL` must be reachable from Render (public URL)
- For localhost, use a tunnel (ngrok, Cloudflare Tunnel) or deploy Weaviate to a cloud provider

---

## Optional: Use Blueprint (render.yaml)

1. `render.yaml` is in the repo root
2. In Render: **New +** → **Blueprint**
3. Connect the repo and select the Blueprint
4. Add env vars in the Blueprint UI (they won’t be in YAML)
5. Render creates the service from the spec

---

## Troubleshooting

### Build fails

- Check **Logs** in the Render dashboard
- Ensure `Dockerfile` and `client/`, `api/` are in the build context
- If root is wrong, set **Root Directory** to `ai_researcher`

### Out of memory (OOM)

- Free tier has 512MB RAM. The cross-encoder reranker (sentence-transformers) uses ~500MB+.
- **Fix:** Set `DISABLE_RERANKER=true` in Render Environment. Retrieval still works with vector search; reranking is skipped.
- Or upgrade to **Starter** ($7/month) for more memory if you want reranking.

### App spins down after 15 minutes

- Free tier spins down after 15 min of inactivity
- First request after spin-down can take ~1 minute
- Upgrade to a paid plan for always-on

### Pipeline fails / Weaviate errors

- Confirm `WEAVIATE_URL` and `WEAVIATE_API_KEY` are correct
- Ensure the Weaviate cluster is running and reachable from Render
- Check Weaviate collection and schema match what the app expects

---

## Post-deploy

- **API docs**: `https://your-app.onrender.com/docs`
- **Health**: `https://your-app.onrender.com/health`
- **Frontend**: served at the same URL (same-origin)
