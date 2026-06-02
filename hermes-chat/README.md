# Hermes Chat

Minimal AI chat app powered by Claude. Vanilla HTML/CSS/JS frontend + Cloudflare Pages Function proxy.

## Stack

- **Frontend**: single `index.html` — no build step
- **API proxy**: `functions/api/chat.js` (Cloudflare Pages Function)
- **Model**: `claude-sonnet-4-6` with prompt caching enabled

## Deploy to Cloudflare Pages

1. Push this directory to a new GitHub repo.
2. In [Cloudflare Pages](https://dash.cloudflare.com), create a new project from that repo.
3. Settings:
   - **Build command**: *(leave empty)*
   - **Output directory**: `/` (root)
4. Add the environment variable / secret:
   - `ANTHROPIC_API_KEY` → your [Anthropic API key](https://console.anthropic.com)
5. Deploy. Done.

## Local dev

Requires [Wrangler](https://developers.cloudflare.com/workers/wrangler/):

```bash
npm install -g wrangler

# Set the API key locally
echo "ANTHROPIC_API_KEY=sk-ant-..." > .dev.vars

# Serve with Pages Functions support
wrangler pages dev . --port 8080
```

Then open `http://localhost:8080`.

## Customise the system prompt

Edit `SYSTEM` in `index.html`:

```js
const SYSTEM = 'You are Hermes, an intelligent and articulate assistant. ...';
```

Or pass a `system` field in the POST body from your own client.
