export async function onRequestGet(context) {
  const schedule = await context.env.ONCALL_SCHEDULE.get("schedule", "json");
  if (!schedule) {
    return Response.json(
      { error: "The on-call schedule has not been published yet." },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }

  return Response.json(schedule, {
    headers: {
      "Cache-Control": "private, no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
