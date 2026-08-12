# Lesson 42 — Responsible AI champion (bonus)

**Level:** Advanced (cross-cutting)  
**Time:** ~150 minutes  
**Prerequisites:** Pack E (23–27) strongly recommended; Packs A–D for context  
**Lab outcome:** Turn Meridian OrderOps into an **RAI-ready system**: scorecard, concrete code/process changes, evidence pack, and a champion checklist you can run every release — plain language, no buzzword theater

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

**Responsible AI (RAI)** means you can show — with artifacts — that OrderOps is:

| Pillar | Plain English | Meridian proof |
|--------|---------------|----------------|
| **Safety** | Hard to make it do harmful/money-wrong things | Red-team ASR, refund plugins |
| **Privacy** | People’s data isn’t spilled or kept forever | Redaction, TTL, DSR |
| **Fairness** | Same situation → same treatment class | Golden parity tests across personas |
| **Transparency** | Humans can see why it acted | Audit narratives, citations, traces |
| **Human control** | People can stop/override | HITL, kill switches, canary rollback |
| **Accountability** | Named owners + evidence | Scorecard, release sign-off |

This bonus lesson **does not** replace counsel or your company’s formal review.  
It makes you the engineer who shows up with **receipts**.

```
RAI scorecard
    │
    ├─ gaps → concrete PRs (plugins, evals, privacy, canary)
    ├─ evidence pack → links to reports/tests
    └─ champion ritual → every release
```

---

## Why this matters

Leadership asks:

> “Are we being responsible with this agent?”

Weak answer: “We use a safe model and have a prompt.”  

Champion answer:

- Here’s last week’s **ASR** (Lesson 23)  
- Here’s **hard_fail_rate** online (Lesson 24)  
- Here’s HITL + **RefundDenyPlugin** (07/26)  
- Here’s **DSR delete** drill (27)  
- Here’s canary abort from the friendlier-prompt experiment (25)  
- Here’s who signed the release  

You are not “the ethics person.” You are the engineer who made responsibility **operable**.

---

## Know these

| Term | Meaning |
|------|---------|
| **RAI** | Responsible AI — practices that keep systems safe, fair, private, controllable, accountable |
| **Scorecard** | Living checklist with pass/fail evidence links |
| **Harm** | Bad outcomes: wrongful refunds, leaked PII, denied help unfairly, unsafe advice |
| **Dual control** | Two parties for high-impact actions (e.g. HITL + tool plugin) |
| **Evidence pack** | Folder of reports proving controls for one release |
| **Champion** | Named human who runs the ritual and blocks “ship anyway” |

---

## Task 1 — Write the Meridian RAI scorecard (v1)

### Why

Without a scorecard, RAI debates become opinion contests.

### Do this

Create `project/meridian_ops/rai/SCORECARD.md`:

```markdown
# Meridian OrderOps — RAI Scorecard

Release: <git_sha>
Owner (champion): <name>
Date:

## Safety
- [ ] Red-team suite v1 ASR == 0 (link: redteam/reports/...)
- [ ] Refund confirm blocked without HITL (plugin test link)
- [ ] No “refund completed” without tool success (judge test)

## Privacy
- [ ] DATA_INVENTORY updated
- [ ] Redaction module on eval + feedback + plugin paths
- [ ] TTL sweep ran this week (log link)
- [ ] DSR export+delete drill within last 90 days

## Fairness / consistency
- [ ] Same WISMO fixture → same tool path for persona A/B lab users
- [ ] No “VIP secret refund” instruction in prompts (grep evidence)

## Transparency
- [ ] Policy answers cite POL-* ids
- [ ] Audit tool jsonl enabled in stage
- [ ] Traces/session ids returned on API errors path

## Human control
- [ ] HITL path exercised this release
- [ ] Canary abort rules documented
- [ ] Kill switch / max-steps still configured

## Accountability
- [ ] MLflow run id on release notes
- [ ] On-call owner named (Lesson 41)
- [ ] Champion sign-off below

Sign-off: __________
```

### Expect

A real file in the repo your team can copy per release.

---

## Task 2 — Baseline: grade OrderOps **today**

### Why

Champions start from truth, not aspiration.

### Do this

Run what you already have:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
export PYTHONPATH=.
# examples — use the commands you actually built in 23–27
python -m meridian_ops.redteam.run_suite
python -m meridian_ops.online_eval.score_inbox
python -m meridian_ops.privacy.run_sweep
pytest meridian_ops/tests/ -q --maxfail=5
```

Fill the scorecard with **pass/fail/unknown**.  
Unknown counts as fail for shipping.

Save a snapshot: `project/meridian_ops/rai/evidence/<date>_baseline/SCORECARD.md`.

### Expect

At least a few honest **fail/unknown** items — that is your backlog.

---

## Task 3 — Close three gaps with concrete changes

### Why

RAI without code/process change is a slide deck.

### Do this

Pick **three** failing scorecard rows and fix them. Suggested menu (choose what your lab still lacks):

1. **Safety:** Register `RefundDenyPlugin` on the FastAPI Runner (Lesson 26) if missing  
2. **Privacy:** Force `purpose` + `redact_text` on online_eval writes (Lesson 27)  
3. **Transparency:** Require policy citation judge in CI for policy agent (Lessons 18/09)  
4. **Human control:** Set canary percent config default to `10` max for prompt experiments (Lesson 25)  
5. **Fairness:** Add eval case pair — same ticket text for `user_id=maya` and `user_id=devon` — expect identical tool trajectory  

For each fix, record:

```markdown
## Gap → Fix
- Scorecard row: ...
- Change: path + summary
- Test: command + result
- Evidence path: rai/evidence/<date>/...
```

in `project/meridian_ops/rai/CHANGELOG_RAI.md`.

### Expect

Three evidence-backed closures; scorecard rows flip to pass.

---

## Task 4 — Fairness / consistent treatment drill

### Why

Retail agents sometimes grow “secret VIP” behavior in prompts. That is a responsibility failure.

### Do this

1. Grep prompts/instructions for `VIP`, `executive`, ` entourage`, `special customer`:  

```bash
rg -n -i "vip|executive|special customer| entourage" project/ --glob '*.py' --glob '*.md'
```

2. If found in agent instructions, remove or gate behind explicit human policy + audit.  
3. Add golden: identical WISMO text for two user ids → same `get_order` tool use (AgentEvaluator or Runner assert).  

### Expect

No hidden VIP money path; parity test in suite.

> **Watch out:** Different **channels** (store vs chat) can have different playbooks — that is OK if documented. Secret prompt favoritism is not.

---

## Task 5 — Transparency pack (explainability humans can use)

### Why

“The model decided” is not an explanation Priya can defend.

### Do this

Build `project/meridian_ops/rai/explain.py` that, given a session’s events + final text, prints:

1. Tools called (ordered)  
2. Policy ids mentioned  
3. Whether HITL was required/approved  
4. One-sentence customer-safe summary  

Run it on a refund HITL session and save output under `rai/evidence/<date>/explain_refund.txt`.

Optional: expose `GET /v1/sessions/{id}/explanation` on your edge (auth required) returning that JSON.

### Expect

A supervisor can reconstruct the story without reading raw tensors.

---

## Task 6 — Human control map (kill switches you can actually pull)

### Why

RAI requires an off switch that is practiced.

### Do this

Create `project/meridian_ops/rai/CONTROL_MAP.md`:

| Risk | Control | How to pull | Who |
|------|---------|-------------|-----|
| Bad prompt | Canary % → 0 | config/flag | on-call |
| Tool abuse | Disable refund tool / plugin deny-all | flag `refunds_enabled=false` | on-call + finance |
| Model outage degrade wrong | Force Flash + no money | Lesson 20 degrade | on-call |
| Privacy incident | Stop sampling + freeze exports | flags | privacy + on-call |
| Agent loop $ burn | max-steps / budget kill | Lesson 07 | on-call |

**Drill:** Flip `refunds_enabled=false` in lab config; prove `request_refund` denied; flip back; log the drill.

### Expect

CONTROL_MAP filled + one drill record with timestamp.

---

## Task 7 — Release evidence pack + champion ritual

### Why

Champions institutionalize the habit.

### Do this

Script or checklist `project/meridian_ops/rai/pack_release.sh` (or a Makefile target) that copies into `rai/evidence/<git_sha>/`:

- redteam report  
- online_eval summary  
- scorecard  
- MLflow run id note  
- CONTROL_MAP drill date  
- pytest JUnit or plaintext log  

Champion ritual (put in SCORECARD footer):

1. Run pack script  
2. Read hard fails  
3. Sign or **block** release  
4. File one improvement ticket if any row scraped by  

Simulate once for this lesson even if you do not ship.

### Expect

A populated `rai/evidence/<sha>/` directory.

---

## Task 8 — “Make us compliant-ready” change list (practical)

### Why

You asked how to change the system to be compliant and RAI-strong. Here is the engineering backlog pattern — implement what is still open in your lab.

### Do this

Ensure these land (implement any missing):

| Change | Where | Why |
|--------|-------|-----|
| Runner plugins: refund deny + PII redact | deploy edge | Enforce safety/privacy globally |
| Online eval redact + purpose + TTL | online_eval/* | Stop PII lakes |
| Feedback + canary abort | feedback/* | Human control on prompt change |
| Red-team in CI | .github/workflows / pytest | Safety gate |
| Citation/grounding judges in CI | evals/judges | Transparency |
| DSR export/delete + audit | privacy/* | Subject rights mechanics |
| No VIP prompt paths + parity eval | agents + evals | Fairness |
| Explanation endpoint or CLI | rai/explain.py | Transparency |
| Feature flags for refunds/sampling | config | Kill switches |
| Scorecard sign-off artifact | rai/evidence | Accountability |

Tick each in `project/meridian_ops/rai/COMPLIANT_READY.md` with links.

### Expect

A single page that maps **change → evidence** for reviewers.

---

## How it works (deeper dive)

RAI is not a separate product stack. It is **Pack E made habitual**:

```
23 attack  → safety evidence
24 online  → living quality + promotion
25 humans  → preferences + canary control
26 plugins → enforceable policy
27 privacy → retention + DSR
42 ritual  → scorecard + sign-off
```

Models will change. Prompts will change.  
The champion keeps the **controls and evidence** from rotting.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Scorecard all green on day one | You were not honest — re-baseline |
| RAI owned only by “ethics slack channel” | Assign engineering champion on-call rotation |
| Evidence pack empty PDFs | Prefer test outputs + json reports |
| Compliance theater docs | Every claim needs a path/command |
| Blocking all innovation | Use canaries + scorecards, not fear |

---

## You are done when

- [ ] SCORECARD.md exists and was baselined honestly  
- [ ] Three gaps closed with CHANGELOG_RAI entries  
- [ ] Fairness grep + parity test done  
- [ ] Explanation artifact produced  
- [ ] CONTROL_MAP + one kill-switch drill recorded  
- [ ] Evidence pack generated for a git sha  
- [ ] COMPLIANT_READY.md ticked with links  

---

## Knowledge check

1. What is an RAI scorecard for?  
2. Name three Meridian pillars and one proof each.  
3. Why is a VIP prompt path an RAI issue?  
4. What does a champion do on release day?  
5. How is this different from “we use a safe model”?

### Answers

1. Turn responsibility into pass/fail evidence per release.  
2. Example: Safety→ASR; Privacy→DSR drill; Human control→canary abort.  
3. Unequal treatment / hidden policy — unfair and unauditable.  
4. Build evidence pack, read fails, sign or block.  
5. Vendor model choice ≠ your tool gates, data handling, or accountability.

---

## Recap — Pack E + bonus

| Lesson | You gained |
|--------|------------|
| 23 | Attack suites + ASR gates |
| 24 | Online sample → score → promote |
| 25 | Labels, preferences, canary rollback |
| 26 | Native plugins as policy middleware |
| 27 | Redact, TTL, DSR mechanics |
| **42** | Scorecard, fixes, evidence, champion ritual |

You can now **defend** Meridian OrderOps as a responsible system — with artifacts, not adjectives.

---

## Stretch goal

Add a quarterly “RAI game day”: inject a synthetic privacy+injection incident; practice CONTROL_MAP pulls; time-to-mitigate < 30 minutes.

---

## Feedback

- Could you run the champion ritual for a friend without this lesson open?  
- Which pillar was weakest in your baseline?  
- Note task number + expected vs actual.

---

## Navigate

**← Pack E** [Lesson 27 — Privacy](27-privacy-retention-compliance.md) · [Lesson 23](23-red-teaming-adversarial-robustness.md)  
**Related ops:** [Lesson 41 — CI/CD & canary](41-cicd-sre-deployment-ops.md)  
**Track home:** [README](../README.md)  
**Next pack:** Lesson 28 — Architecture patterns catalog
