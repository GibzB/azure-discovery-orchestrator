# From Idea to Live: How We Built and Deployed an AI Architecture Consultant in Days

*Posted on the Kiro Blog · June 2026*

---

Selling Azure cloud architecture used to start with weeks of back-and-forth. Sales engineers would schedule discovery calls, take notes, write up requirements, and eventually hand off a slide deck that was already half-outdated by the time the client read it. The whole process was slow, expensive, and frustratingly manual.

What if the entire discovery workshop could happen in a single conversation — and the architecture report wrote itself?

That was the idea behind **Azure Discovery Orchestrator**, an AI-powered tool that replaces the traditional pre-sales discovery call with a seamless, voice-driven conversation. A client speaks naturally about their business, and a multi-agent AI system — backed by GPT-4.1, Azure AI Search, Cosmos DB, and Azure Speech Services — listens, asks smart follow-up questions, and generates a professional architecture recommendation report on the spot.

Building it was one thing. Deploying it to production was another.

---

## The Challenge

The project spanned eleven Azure services, three deployment pipelines, a containerised Python backend, a React frontend, and a team working across GitHub and Azure DevOps simultaneously. Getting all of that to work together — reliably, repeatably, and without breaking anything already running — is the kind of problem that turns a good idea into a long weekend.

A few specific headaches stood out early:

- The target subscription was an **Azure for Students** account with regional policy restrictions. Services that worked in East US were blocked. Models that should have had quota had zero.
- Every push to `main` triggered six pipelines at once, causing race conditions where two infrastructure deployments would fight over the same ARM deployment slot.
- Docker builds were failing because a Linux audio library (`libasound2`) had been silently renamed in the base image's Debian release.
- GitHub Actions kept rejecting service connections because the university tenant blocked app registrations entirely.

Each of these felt like a wall. With Kiro, they became speed bumps.

---

## How Kiro Helped

Kiro worked through every layer of the stack — not just writing code, but reasoning through the constraints of the environment and finding the right path forward.

**Infrastructure as Code.** Kiro generated all eleven Bicep modules from scratch — OpenAI, Speech, AI Search, Cosmos DB, Key Vault, Storage, Container Apps, Monitoring, and more — with secure defaults, `@secure()` decorators on sensitive outputs, and environment-specific parameter files for dev, test, and prod.

**Pipeline design.** When GitHub Actions OIDC login failed (blocked by the tenant), Kiro created a user-assigned managed identity, assigned it Contributor on the subscription, and wired up Workload Identity Federation credentials for both GitHub Actions and Azure DevOps — without needing an app registration.

**Race condition fixes.** When concurrent deployments started colliding, Kiro added polling loops to each pipeline that wait for active ARM deployments to clear before proceeding, and added `exit 1` guards so a failed Container App state actually stops the pipeline instead of silently letting the next step run against a broken resource.

**Debugging live failures.** When the Container App kept crashing with a startup probe failure, Kiro queried Log Analytics directly, identified the Python traceback (`speechsdk.SpeechConfig()` crashing on an empty key at import time), and refactored the Speech SDK to initialise lazily — fixing the crash without touching any other service.

**UI redesign.** Kiro rebuilt the entire frontend interface — dark glass morphism, animated voice orb with dual pulse rings, a live transcript panel, a four-phase discovery progress tracker, and a professional footer linking back to the GitHub repo — all passing TypeScript strict mode on the first check.

---

## The Result

In the space of a few days, the Azure Discovery Orchestrator went from a folder of empty files to a fully deployed, production-grade system:

- **Ten Azure resources** live in `italynorth`, all provisioned by Bicep
- **Three CI/CD pipelines** in Azure DevOps and three in GitHub Actions, all green
- **Voice-to-voice conversations** — a client speaks, the AI consultant responds in natural speech
- **Automated report generation** at the end of every session
- **ACR image retention** keeping storage usage minimal with automatic pruning on every deploy

The tool that used to take weeks of human effort now takes a single conversation.

---

*Azure Discovery Orchestrator is open source. You can explore the full codebase, architecture docs, and CI/CD setup at [github.com/GibzB/azure-discovery-orchestrator](https://github.com/GibzB/azure-discovery-orchestrator).*
