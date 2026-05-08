# ============================================
# GODFALL - run.py - The Ignition Switch
# ============================================
# This is the file you run to start the dev
# server. Think of it like turning the key on
# the Falcon — it doesn't DO much itself, but
# nothing happens without it.
#
# Run it with:
#   python run.py
# ============================================

# "import" is how Python brings in tools from
# other files/packages. It's like calling crew
# to the bridge — "Uvicorn, report for duty."
import uvicorn

# This is Python's way of saying:
# "Only run this code if YOU are the file
# being executed directly."
#
# Why? Because sometimes files get imported
# by OTHER files. This guard ensures the
# server only starts when you intentionally
# run this file — not when something else
# just references it.
#
# Star Wars parallel: It's like a safety
# switch on a thermal detonator. You don't
# want it going off just because someone
# picked it up.
if __name__ == "__main__":

    # uvicorn.run() launches the server.
    # Let's break down what we're telling it:
    #
    # "app.main:app"
    #   → Go into the app/ folder,
    #     find main.py,
    #     and grab the object called 'app'
    #     (which will be our FastAPI instance)
    #
    # host="127.0.0.1"
    #   → Only accept connections from THIS
    #     machine (localhost). Since the site
    #     is private, we don't need outside
    #     access during development.
    #
    # port=8000
    #   → The "docking port" — you'll visit
    #     http://127.0.0.1:8000 in your
    #     browser to see the site.
    #
    # reload=True
    #   → Auto-restart the server whenever
    #     you save a file. R2 rerouting power
    #     in real-time so you never have to
    #     manually restart during development.
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )