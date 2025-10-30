# LiveKit Agent Debugging Skill

Use this skill when debugging LiveKit agent issues, before making code changes to agent components (TTS, STT, LLM), or when deployment appears to fail despite code changes.

## When to Use This Skill

**MANDATORY use cases:**
- Agent is stuck at "setting things up" or failing to connect
- User reports errors in production but logs aren't clear
- Making changes to TTS, STT, LLM, or plugin configurations
- After deployment but old errors persist
- TypeError or initialization errors in production logs
- Before deploying any agent code changes

**DO NOT use for:**
- Simple code changes unrelated to agent initialization
- Documentation updates
- Frontend-only changes

## Critical Rule: Console Mode First

**NEVER make agent code changes without testing in console mode first.**

Console mode reveals initialization errors immediately that won't appear in production logs until after deployment. This single step prevents 90% of deployment issues.

## Systematic Debugging Process

### Phase 1: Verify Current State

Before making any changes, establish baseline understanding:

1. **Check agent status:**
   ```bash
   cd my-app
   lk agent status
   ```

   Expected output:
   - Status: Running
   - Active replicas: 1 or more
   - Recent deployment time

   If status is not "Running" or replicas = 0, agent is down.

2. **Check recent logs for errors:**
   ```bash
   lk agent logs 2>&1 | grep -E "(Error|TypeError|ValueError|error)" | tail -20
   ```

   Common error patterns:
   - "TypeError: __init__() got an unexpected keyword argument" → Plugin API mismatch
   - "missing 1 required keyword-only argument" → Plugin version bug
   - No recent logs at all → Worker shut down or not running

3. **Check installed plugin versions:**
   ```bash
   uv pip list | grep livekit
   ```

   Note the versions of:
   - livekit-agents
   - livekit-plugins-elevenlabs (or other TTS plugins)
   - livekit-plugins-openai
   - livekit-plugins-deepgram (or other STT plugins)

### Phase 2: Test in Console Mode

**This is the most critical step.** Console mode shows the actual initialization error.

```bash
cd my-app
uv run python src/agent.py console
```

**What to look for:**
- Does it start without errors? → Agent initialization is fine, issue is elsewhere
- TypeError on plugin init? → Plugin API incompatibility
- Import errors? → Missing dependencies
- Configuration errors? → Check .env.local or plugin parameters

**If console mode fails:**
1. Read the full error traceback carefully
2. Identify the exact line and parameter causing the issue
3. Check the plugin version and consult LiveKit docs for correct API
4. Fix the code
5. Test in console mode again
6. Repeat until console mode starts successfully

**If console mode succeeds but production fails:**
- Issue is likely environment-specific (secrets, Docker cache, or network)
- Proceed to Phase 3

### Phase 3: Check for Docker Cache Issues

Docker caching can prevent code deployment even after git commits.

1. **Check build logs for cache indicators:**
   ```bash
   lk agent logs --log-type=build | grep -A 2 "COPY . ."
   ```

   Look for:
   - `#X CACHED` → Code was NOT deployed, using old cached version
   - `#X DONE 0.Xs` → Code WAS deployed successfully

2. **If code was cached (not deployed):**
   ```bash
   # Bust the cache by modifying .dockerignore
   echo "# Force rebuild $(date) - Fix <issue description>" >> my-app/.dockerignore

   # Commit and deploy
   cd my-app
   git add .dockerignore
   git commit -m "Bust Docker cache: Fix <issue>"
   lk agent deploy
   ```

3. **Verify the new deployment copied code:**
   ```bash
   lk agent logs --log-type=build | grep -A 2 "COPY . ."
   ```

   Should see `DONE` not `CACHED`.

### Phase 4: Plugin API Compatibility

If console mode revealed plugin API errors:

1. **Identify the plugin and version:**
   ```bash
   uv pip list | grep <plugin-name>
   ```

2. **Check LiveKit docs for correct API:**
   Use the LiveKit MCP server to get current documentation:
   - Query: "How do I configure <plugin> TTS/STT?"
   - Look for code examples in current docs

3. **Common API changes to watch for:**

   **ElevenLabs TTS:**
   - v0.7.x: `voice=elevenlabs.Voice(id="...", name="...", category="...")`
   - v1.2+: `voice_id="..."` (string parameter)

   **OpenAI:**
   - Check if model names changed (e.g., gpt-4o-mini vs gpt-4.1-mini)

   **Deepgram:**
   - API versions in URL path may have changed

4. **Update pyproject.toml if needed:**
   ```bash
   # Update to specific version
   uv add "livekit-plugins-elevenlabs>=1.2.0"

   # Or pin exact version
   uv add "livekit-plugins-elevenlabs==1.2.15"
   ```

5. **Test the change in console mode:**
   ```bash
   uv run python src/agent.py console
   ```

### Phase 5: Deploy and Verify

Only deploy after console mode succeeds:

1. **Bust Docker cache if needed** (see Phase 3)

2. **Deploy:**
   ```bash
   cd my-app
   lk agent deploy
   ```

3. **Restart the agent:**
   ```bash
   lk agent restart
   ```

   **Why restart?** Workers load configuration at startup. Restart ensures new code is used.

4. **Wait for new worker to start:**
   ```bash
   lk agent status
   ```

   Wait until "Deployed At" timestamp updates (usually ~30 seconds).

5. **Monitor logs for initialization:**
   ```bash
   lk agent logs | grep -E "(registered worker|process initialized|Error|TypeError)"
   ```

   Expected: "registered worker" and "process initialized" messages
   Concerning: Any Error or TypeError messages

6. **Test with Agent Playground or console:**
   - Open LiveKit Cloud Dashboard → Agents → Your Agent → Test
   - Or connect via console mode: `uv run python src/agent.py console`

## Red Flags That Require This Skill

Stop and use this skill immediately if you see:

- ❌ "Agent stuck at setting things up"
- ❌ TypeError or ValueError in production logs
- ❌ "missing 1 required keyword-only argument"
- ❌ "got an unexpected keyword argument"
- ❌ Old errors persist after deploying fixes
- ❌ Build logs show `#X CACHED` for code copy step
- ❌ User can't connect to agent after deployment

## Success Criteria

You've completed this skill successfully when:

- ✅ Console mode starts without errors
- ✅ Production logs show "registered worker" and "process initialized"
- ✅ Build logs show `DONE` (not CACHED) for code copy
- ✅ Agent status shows Running with active replicas
- ✅ Test connection succeeds via Agent Playground or console
- ✅ No TypeError or initialization errors in logs

## Common Mistakes to Avoid

1. **Deploying without testing console mode first**
   - Result: Slow deploy-test-fix cycle, wasted time
   - Fix: ALWAYS test console mode before deploying

2. **Ignoring Docker cache**
   - Result: Old broken code runs despite fixes
   - Fix: Check build logs, bust cache if needed

3. **Not restarting after deployment**
   - Result: Old workers keep running with old code
   - Fix: Always run `lk agent restart` after deploy

4. **Guessing at plugin APIs**
   - Result: Wrong configuration, more errors
   - Fix: Consult LiveKit docs via MCP server

5. **Not checking plugin versions**
   - Result: API incompatibility, confusion about why code fails
   - Fix: Run `uv pip list | grep livekit` before debugging

## Quick Reference Commands

```bash
# Status and logs
lk agent status
lk agent logs
lk agent logs --log-type=build

# Testing
cd my-app
uv run python src/agent.py console
uv run pytest

# Version checking
uv pip list | grep livekit

# Deployment
cd my-app
echo "# Force rebuild $(date) - Fix issue" >> .dockerignore
lk agent deploy
lk agent restart

# Monitoring post-deploy
lk agent logs | grep -E "(registered worker|Error|TypeError)"
```

## Post-Incident Learning

After resolving an issue with this skill, update:

1. **CLAUDE.md** if new patterns emerged
2. **my-app/AGENTS.md** if agent-specific learnings
3. **This skill** if process improvements identified

Remember: The goal is to prevent these errors entirely through console mode testing, not just fix them after they occur in production.
