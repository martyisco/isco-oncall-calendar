export async function handleSchedule(env) {
  const schedule = await env.ONCALL_SCHEDULE.get("schedule", "json");
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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const host = request.headers.get("host") || url.hostname;
    if (host.includes("workers.dev") || url.hostname.includes("workers.dev")) {
      return new Response("Not found", { status: 404 });
    }
    if (url.pathname === "/api/schedule") {
      return handleSchedule(env);
    }
    return env.ASSETS.fetch(request);
  },
};
