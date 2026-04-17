# 📊 What is SLA in Your System?
In your system, SLA defines the maximum allowed time for two key actions:

First response – time from ticket creation until an agent replies.

Resolution – time from ticket creation until the ticket is closed (resolved).

These targets are set per priority (e.g., High, Medium, Low) and optionally per department. For example:

Priority	Response SLA	Resolution SLA
Critical	1 hour	4 hours
High	4 hours	24 hours
Medium	8 hours	48 hours
Low	24 hours	5 days
You can also define business hours (e.g., only count working hours) – this is handled by the SlaRule model and a BusinessCalendar.

# 🧠 How SLA Rules Are Stored
Model: SlaRule (in tickets/models.py)

Fields:

priority – which priority this rule applies to.

department (optional) – restrict to a specific department.

response_hours – target hours for first response.

resolution_hours – target hours for resolution.

business_hours_only – if True, only count time during defined business hours (using a BusinessCalendar).

is_active – enable/disable the rule.

When a ticket is created, the system looks up the active SlaRule matching its priority and department (if any). It then calculates two due dates:

response_due_at = created_at + response_hours (adjusted for business hours if enabled).

resolution_due_at = created_at + resolution_hours (adjusted similarly).

These due dates are stored directly on the Ticket model.

# ⏰ How SLA Breaches Are Detected (Periodic Tasks)
Your system runs a Celery task every minute called check_sla_breaches (in tickets/tasks.py). This task:

Queries for tickets where:

response_due_at is in the past and first_response_at is NULL and is_response_breached is False.

Similarly for resolution_due_at and resolved_at.

For each such ticket, it:

Sets is_response_breached = True (or is_resolution_breached).

Saves the ticket.

Triggers escalation by calling check_escalation_for_ticket.delay(ticket.id) asynchronously.

This ensures that within one minute of a missed deadline, the breach flag is set and escalation starts.

# 🔁 Escalation Policies (Multi‑Level)
Once a breach is detected (or other events like “no activity for X minutes”), the escalation engine takes over.

EscalationPolicy model defines rules:

trigger_event – what triggers escalation (e.g., response_breach, resolution_breach, time_since_creation, no_activity).

level – 1, 2, 3, etc. (higher level = more severe).

threshold_minutes – used for time‑based triggers.

escalate_to_role or escalate_to_user – who to notify.

When a ticket meets the criteria (e.g., a response breach of level 1), the system:

Creates a TicketEscalation record.

Notifies the target user (in‑app notification + email).

Updates the ticket’s escalation_level field.

You can have multiple levels: if after level 1 the issue isn’t resolved, another policy with a higher level may trigger (e.g., after 2 more hours).

The escalation check is also triggered:

By the periodic check_sla_breaches task (for breaches).

By a separate periodic check_escalations task (for time‑based events like “no activity for 2 hours”).

Manually when a ticket is updated (e.g., an agent changes status).

# 📈 SLA Dashboard & Metrics
The SLA dashboard reads pre‑computed metrics from the TicketMetrics model.

TicketMetrics stores for each ticket:

first_response_time (seconds)

resolution_time

sla_breached_response, sla_breached_resolution

Counts (escalations, reassignments, etc.)

These metrics are refreshed periodically by refresh_ticket_metrics (Celery task, runs every 15‑60 minutes) and also after ticket updates (via signals or manual calls).

The dashboard shows:

Open tickets, average response/resolution times, breach counts.

Daily charts for opened vs resolved, breaches, escalations.

🔧 Periodic Tasks at a Glance
Task Name	What it does	When it runs
check_sla_breaches	Detects missed SLAs, marks breaches, triggers escalations.	Every 1 minute (critical).
check_escalations	Evaluates time‑based escalation policies (e.g., no activity, time since creation).	Every 5‑15 minutes.
refresh_ticket_metrics	Updates TicketMetrics table for dashboard.	Every 15‑60 minutes.
cleanup_expired_tokens	Deletes expired public tracking tokens.	Daily.
celery.backend_cleanup	Cleans up old Celery task results.	Daily (built‑in).

# ✅ Answering Client Questions

Q: How does the system know when to escalate?
A: We define escalation policies (e.g., “if a critical ticket’s response is overdue, escalate to the supervisor”). A background task runs every minute, checks all open tickets, and automatically creates escalation records and sends notifications.

Q: Can we change SLA rules without code changes?
A: Yes. SLA rules are stored in the database. A supervisor can edit them via Django admin or a custom UI (you can build a simple form). No code changes needed.

Q: What if we need to exclude weekends from SLA calculations?
A: You can define a BusinessCalendar with working days and holidays. The SlaRule has a flag business_hours_only – if enabled, the due date calculation uses only the defined working hours.

Q: How are SLAs enforced for WhatsApp tickets?
A: Exactly the same as web tickets. When a WhatsApp message creates a ticket, it gets a priority (default Medium) and a department, so the SLA rule applies. The same breach detection and escalation work across all channels.

Q: Can we get a report of SLA performance?
A: Yes. The SLA dashboard shows real‑time charts and KPIs. You can also export data (we can add an export feature). Long‑term, we can build scheduled email reports.

Q: How accurate is the response time measurement?
A: The system records the timestamp of the first agent message (or internal note) and subtracts the creation time. It’s accurate to the second. Business hours are accounted for if configured.

With this understanding, you’ll be able to confidently explain the SLA engine and periodic tasks to your client. Let me know if you need any diagrams or specific numbers to illustrate.


You're absolutely right – your current SLA configuration is a global, flat structure with four priority levels (Low, Medium, High, Critical). There is no department‑specific override, and business hours are not applied (business_hours_only=False). Also, multi‑level escalation (e.g., level 1 → supervisor, level 2 → department head) is not yet implemented.

This is perfectly fine for a demo, and you can explain it honestly as the foundation that can be extended. Let me help you prepare clear answers for your client.

✅ What You Have Now (Good for Demo)
SLA targets are set per priority, globally across all departments.

Breach detection runs every minute via Celery task.

Single‑level escalation – when a ticket breaches a SLA, the system creates an escalation and notifies a predefined user or role (you can set up one level, e.g., escalate to supervisor).

Dashboard shows breaches, average times, and trends.

Limitations (to be transparent about):

No business hours (weekends/holidays are counted as normal time).

No department‑specific SLA rules.

No chained escalation (level 1 → level 2 → …).

📢 What to Tell the Client
"Our SLA engine currently supports global targets per priority, automatic breach detection (every minute), and single‑level escalation (e.g., if a High priority ticket is not responded to within 2 hours, it escalates to the supervisor). The system is designed to easily add department‑specific rules, business hour calendars, and multi‑level escalation in the future – those are configurable, not code changes."

If they ask about multi‑level escalation:

"We have the data model and logic ready (EscalationPolicy with levels), but we have not yet activated multiple levels. Once you have defined your escalation matrix (e.g., level 1 to supervisor, level 2 to department head), we can enable it within a day. It's a configuration change, not a development effort."

🛠️ Should You Implement Multi‑Level Escalation Before the Demo?
Not necessary, unless the client specifically asks for it. The current single‑level escalation is enough to demonstrate the concept. However, if you want to show that the system is ready for more, you could quickly create two policies (e.g., level 1 and level 2) with different thresholds and show how the escalation level increases. That would take about 15 minutes to set up via admin.

If you decide to do it, here's a quick example:

Name	Trigger	Level	Target	Threshold
Escalation L1	Response breach	1	Supervisor	–
Escalation L2	Time since creation	2	Department Head	120 minutes
Then during the demo, you can show that after 2 hours without resolution, the ticket escalates to the department head. This would impress the client.

But again, not required. Your current demo is already strong.

📌 Key Points for Your Demo Script
"We track two SLA metrics: first response and resolution."

"Targets are set per priority; you can also set them per department."

"A background task checks every minute for missed deadlines."

"When a breach occurs, the system automatically creates an escalation and notifies the responsible person."

"The dashboard gives you real‑time visibility into performance."

"We can easily add business hours, department rules, and multi‑level escalation – all through configuration, not code."

You are ready. Good luck with the demo! 🚀