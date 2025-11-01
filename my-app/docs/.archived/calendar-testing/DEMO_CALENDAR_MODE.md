# Demo Mode for Calendar Booking (No Google Calendar Required)

If you can't grant calendar permissions due to corporate restrictions, you can run in demo mode.

## Quick Demo Mode

Add this to your `.env.local`:
```bash
DEMO_MODE=true
```

Then modify the `book_sales_meeting` function to check for demo mode:

```python
async def book_sales_meeting(self, ...):
    """Book a sales meeting."""

    # Check for demo mode
    if os.getenv("DEMO_MODE") == "true":
        # Simulate successful booking without actual calendar
        meeting_time = self._parse_meeting_time(preferred_date, preferred_time)

        # Log the booking details
        logger.info(
            f"DEMO MODE - Would create calendar event:\n"
            f"  Title: PandaDoc Sales Consultation - {customer_name}\n"
            f"  Email: {customer_email or self.user_email}\n"
            f"  Time: {meeting_time}\n"
            f"  Qualifications: {self.discovered_signals}"
        )

        # Write to a file for verification
        with open("demo_bookings.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - Booking for {customer_name} at {meeting_time}\n")

        return {
            "booking_status": "confirmed",
            "meeting_time": meeting_time.strftime("%A, %B %d at %I:%M %p %Z"),
            "meeting_link": "https://meet.google.com/demo-meeting-link",
            "calendar_event_id": f"demo_{int(datetime.now().timestamp())}",
            "action": "meeting_booked",
            "demo_mode": True
        }

    # Regular calendar creation code continues...
```

This allows you to:
- Test the complete flow without calendar permissions
- Verify the tool is being called
- See what would be booked
- Check the `demo_bookings.log` file for proof