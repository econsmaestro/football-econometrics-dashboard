import streamlit as st

st.set_page_config(
    page_title="Agile Notes",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Agile Notes")
st.caption("Study notes from the LinkedIn Learning — Agile Foundations course (4.7 ★, 38,791 reviews)")

tab1, = st.tabs(["Agile Fundamentals"])

with tab1:
    st.header("Agile Fundamentals")
    st.markdown("---")

    # ── Chapter 2 ──────────────────────────────────────────────────────────────
    with st.expander("2. Have an Agile Mindset", expanded=True):
        st.subheader("The Agile Manifesto: Values")
        st.markdown("""
The Agile Manifesto (2001) prioritises **four core values**:

| Over... | We value... |
|---------|-------------|
| Processes and tools | **Individuals and interactions** |
| Comprehensive documentation | **Working software** |
| Contract negotiation | **Customer collaboration** |
| Following a plan | **Responding to change** |

> The items on the right are still valuable — Agile simply values the items on the **left more**.
""")

        st.subheader("The Agile Manifesto: 12 Principles")
        st.markdown("""
1. Satisfy the customer through **early and continuous delivery** of valuable software.
2. **Welcome changing requirements**, even late in development.
3. Deliver working software **frequently** (weeks, not months).
4. Business people and developers must **work together daily**.
5. Build projects around **motivated individuals**; trust them.
6. **Face-to-face conversation** is the most efficient communication.
7. **Working software** is the primary measure of progress.
8. Agile promotes **sustainable development** — a constant pace indefinitely.
9. Continuous attention to **technical excellence** and good design.
10. **Simplicity** — maximising the work not done — is essential.
11. **Self-organising teams** produce the best architectures, requirements, and designs.
12. Teams **regularly reflect and adjust** their behaviour to become more effective.
""")

    # ── Chapter 3 ──────────────────────────────────────────────────────────────
    with st.expander("3. Individuals and Interactions", expanded=True):
        st.subheader("The Cost of Multitasking")
        st.markdown("""
- Switching between tasks carries a **cognitive switching penalty** — the brain takes time to re-load context.
- Every task switch adds overhead; completing tasks **sequentially** is faster overall than juggling many at once.
- Agile teams **limit work-in-progress (WIP)** to reduce multitasking waste.
""")

        st.subheader("Avoid Work Handoffs")
        st.markdown("""
- Every time work is handed from one person/team to another, **information is lost** and delays are introduced.
- Handoffs create queues — work sits idle waiting for the next person.
- **Cross-functional teams** that own end-to-end delivery minimise handoff costs.
- Key exercise: *Understand the cost of adding handoffs at work* — mapping handoffs reveals hidden waste.
""")

        st.subheader("The Penny Game")
        st.markdown("""
- A classic Agile simulation: flip coins in large batches vs. small batches.
- **Small batches** deliver value faster and expose problems earlier.
- Demonstrates that **flow efficiency** matters more than keeping everyone busy.
- Core takeaway: release frequently in small increments rather than one big release.
""")

        st.subheader("Writing Better User Stories")
        st.markdown("""
User stories capture requirements from the **user's perspective**:

```
As a <type of user>,
I want <some goal>,
so that <some reason>.
```

**INVEST criteria** for good user stories:
- **I**ndependent — can be developed in any order
- **N**egotiable — details are open to discussion
- **V**aluable — delivers value to the user or business
- **E**stimable — team can size the story
- **S**mall — fits in a single sprint
- **T**estable — clear acceptance criteria

**Acceptance criteria** define when a story is "done" — written as *Given / When / Then* scenarios.
""")

    # ── Chapter 4 ──────────────────────────────────────────────────────────────
    with st.expander("4. Deliver Working Software", expanded=True):
        st.subheader("Start with the Highest Value")
        st.markdown("""
- Prioritise the **backlog by business value** — tackle the most valuable items first.
- Avoids spending months building low-value features.
- Stakeholders should continuously re-prioritise as understanding grows.
- Technique: use a **Priority Matrix** (value vs. effort) to identify quick wins.
""")

        st.subheader("Prioritise with a Taskboard")
        st.markdown("""
- A **taskboard** (physical or digital) makes work visible: columns typically include *To Do → In Progress → Done*.
- Teams pull work rather than having it pushed to them.
- Limits WIP and surfaces bottlenecks immediately.
- Popular tools: Jira, Trello, physical sticky notes on a wall.
""")

        st.subheader("Avoid PowerPoint — Deliver Working Software")
        st.markdown("""
- Slide decks are **documentation, not delivery** — they don't prove the software works.
- Agile favours **demos of working software** over status reports and presentations.
- "Control Culture" trap: organisations that demand reports and approvals slow teams down and conflict with agile ways of working.
- Rule of thumb: if you can demo it, demo it instead of presenting slides about it.
""")

    # ── Chapter 5 ──────────────────────────────────────────────────────────────
    with st.expander("5. Respond to Change", expanded=True):
        st.subheader("Inspect and Adapt")
        st.markdown("""
- Agile teams hold regular **retrospectives** to inspect what happened and adapt their process.
- The inspect-and-adapt loop is at the heart of empirical process control.
- Three pillars of Scrum: **Transparency**, **Inspection**, **Adaptation**.
- Don't wait until the end of the project to learn — build feedback loops into every sprint.
""")

        st.subheader("Stay Within Timeboxes")
        st.markdown("""
- A **timebox** is a fixed period of time during which work must be completed.
- Timeboxes create urgency, force prioritisation, and prevent endless debate.
- Examples: 2-week sprints, 15-minute daily standups, 1-hour sprint reviews.
- If work isn't done by the timebox end, the scope is cut — **not the deadline**.
""")

        st.subheader("Jump Off the Waterfall")
        st.markdown("""
- **Waterfall** is sequential: Requirements → Design → Build → Test → Deploy — each phase gates the next.
- Problems surface **late** in waterfall when they are expensive to fix.
- Agile delivers in iterative cycles so problems are found **early and cheaply**.
- Transition tip: start with one team or one project rather than a big-bang transformation.
""")

        st.subheader("Commit to Sprints")
        st.markdown("""
- A **sprint** (or iteration) is a short, fixed-length cycle (typically 1–4 weeks).
- The team commits to a **sprint goal** at the start; the scope is frozen for the sprint duration.
- At the end of each sprint, potentially shippable software is produced.
- Sprints provide a **regular rhythm** (cadence) that synchronises the team and stakeholders.
""")

    # ── Chapter 6 ──────────────────────────────────────────────────────────────
    with st.expander("6. Popular Agile Frameworks", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("🔄 Scrum")
            st.markdown("""
**Roles**
- Product Owner
- Scrum Master
- Development Team

**Events**
- Sprint Planning
- Daily Scrum (standup)
- Sprint Review
- Sprint Retrospective

**Artifacts**
- Product Backlog
- Sprint Backlog
- Increment

Sprints are fixed at **1–4 weeks**. The team self-organises around sprint goals.
""")

        with col2:
            st.subheader("⚡ Extreme Programming (XP)")
            st.markdown("""
XP focuses on **engineering practices**:

- **Test-Driven Development (TDD)** — write tests before code
- **Pair Programming** — two developers, one keyboard
- **Continuous Integration** — merge and build frequently
- **Refactoring** — continuously improve code quality
- **Simple Design** — do the simplest thing that works
- **Small Releases** — deploy often
- **Collective Code Ownership** — anyone can change any code
- **On-site Customer** — customer is always available

Best for teams needing high code quality.
""")

        with col3:
            st.subheader("📌 Kanban")
            st.markdown("""
Kanban is a **flow-based** method:

- Visualise all work on a **Kanban board**
- **Limit WIP** per column to expose bottlenecks
- Manage and improve **flow** (cycle time, throughput)
- Make policies **explicit**
- Implement **feedback loops**
- Improve **collaboratively**

No fixed iterations — work flows continuously. Great for **operations, support, and maintenance** teams.

Key metric: **Lead Time** (time from request to delivery).
""")

    # ── Chapter 7 ──────────────────────────────────────────────────────────────
    with st.expander("7. Improve Customer Collaboration", expanded=True):
        st.subheader("Common Roles on an Agile Team")
        st.markdown("""
| Role | Responsibility |
|------|----------------|
| Product Owner | Owns the backlog; prioritises work; represents the customer |
| Scrum Master | Servant-leader; removes impediments; coaches the team |
| Developer / Team Member | Cross-functional; designs, builds, tests |
| Stakeholder | Provides feedback; attends sprint reviews |
| UX Designer | Ensures the product meets user needs |
""")

        st.subheader("The Product Owner")
        st.markdown("""
- **Single** accountable person for the product backlog.
- Balances business value, technical constraints, and user needs.
- Must be **available** to the team to answer questions quickly.
- Defines acceptance criteria and accepts or rejects sprint output.
- Not the same as a Project Manager — the PO is focused on *what* to build, not *how* to manage the project.
""")

        st.subheader("The Scrum Master")
        st.markdown("""
- Acts as a **servant-leader** — serves the team, not manages it.
- Removes **impediments** that block the team's progress.
- Coaches the team and organisation on Scrum practices.
- Facilitates Scrum ceremonies without dominating them.

**Scrum Master vs Project Manager:**
| Scrum Master | Project Manager |
|---|---|
| Servant-leader | Command-and-control |
| Removes impediments | Assigns tasks |
| Protects the team | Reports upward |
| No formal authority | Formal authority |
""")

        st.subheader("Combat Groupthink")
        st.markdown("""
- **Groupthink** occurs when the desire for harmony overrides honest evaluation.
- Symptoms: no one raises concerns; everyone agrees too quickly; risk is downplayed.
- Countermeasures: **anonymised voting**, devil's advocate role, safe retrospectives.
- Planning Poker is one tool that surfaces individual estimates before group discussion.
""")

        st.subheader("Planning Poker")
        st.markdown("""
- A **consensus-based estimation** technique using Fibonacci-like cards (1, 2, 3, 5, 8, 13, 20, 40, 100, ∞, ?).
- Each team member picks a card for the story size simultaneously — **prevents anchoring**.
- Outliers explain their reasoning → discussion → re-vote until consensus.
- Forces everyone to think independently before sharing, reducing groupthink.
- Estimates are in **story points** (relative size), not hours.
""")

    # ── Chapter 8 ──────────────────────────────────────────────────────────────
    with st.expander("8. Start an Agile Transformation", expanded=True):
        st.subheader("Major Agile Challenges")
        st.markdown("""
Common obstacles when adopting Agile:

| Challenge | Why It Happens |
|-----------|----------------|
| **Lack of executive support** | Leaders don't see tangible ROI quickly enough |
| **Resistance to change** | Teams comfortable with existing processes |
| **Control culture** | Management wants detailed plans and status reports |
| **Distributed teams** | Face-to-face collaboration is harder |
| **Legacy systems** | Continuous delivery is blocked by slow release processes |
| **Scaling** | Agile works for one team; coordinating many teams is harder |

> The biggest single predictor of agile failure is **insufficient executive sponsorship**.
""")

        st.subheader("How to Start an Agile Transformation")
        st.markdown("""
**Step-by-step approach:**

1. **Start small** — pilot with one willing team rather than rolling out org-wide at once.
2. **Get a sponsor** — secure a senior leader who will protect the team from old-school demands.
3. **Train the team** — ensure everyone understands agile values, not just mechanics.
4. **Establish a cadence** — fixed sprint length, regular ceremonies, clear Definition of Done.
5. **Create safety** — teams must be able to surface problems without fear of blame.
6. **Measure outcomes, not activity** — track delivered value and customer satisfaction, not hours worked.
7. **Inspect and adapt the transformation itself** — retrospect on the change process, not just the work.

> Don't try to do "Agile in name only" — cargo-culting rituals without the mindset will fail.
""")

    # ── Conclusion ─────────────────────────────────────────────────────────────
    with st.expander("Conclusion: Continuing with Agile", expanded=False):
        st.markdown("""
- Agile is a **journey, not a destination** — teams continuously improve.
- Deepen knowledge through frameworks like **Scrum, Kanban, SAFe, LeSS, or Nexus** for scaling.
- Relevant certifications: **CSM** (Certified ScrumMaster), **CSPO** (Certified Scrum Product Owner), **PMI-ACP**, **PSM** (Professional Scrum Master).
- Keep revisiting the **Agile Manifesto** — values and principles over processes and tools.
- Build a culture of **psychological safety**, **transparency**, and **continuous learning**.
""")

    st.markdown("---")
    st.caption("Source: LinkedIn Learning — Agile Foundations | 4.7 ★ (38,791 reviews)")
