import io, segno, os
HERE=os.path.dirname(os.path.abspath(__file__))

RAMP = ["#13314f","#2d5a82","#4d82a8","#7aa6c4","#a9803f","#c6a463","#ddd6c6"]

def qr(data,color="#13314f"):
    b=io.BytesIO()
    segno.make(data,error='m').save(b,kind='svg',scale=10,border=2,dark=color,light=None,xmldecl=False,svgns=True)
    return b.getvalue().decode().strip().replace('width="330" height="330"','width="100%" height="100%"')

AVATAR = open(os.path.join(HERE,'avatar.svg')).read().replace('width="200" height="200"','width="100%" height="100%"')

def conic(alloc):
    stops=[];cum=0
    for i,(_,pct,_) in enumerate(alloc):
        stops.append(f"{RAMP[i]} {cum}% {cum+pct}%");cum+=pct
    return "background:conic-gradient("+",".join(stops)+");"

def legend(alloc):
    rows=""
    for i,(cat,pct,gb) in enumerate(alloc):
        rows+=(f'<tr><td class="sw"><span class="swatch" style="background:{RAMP[i]}"></span></td>'
               f'<td class="cat">{cat}</td><td class="pct">{pct}%</td><td class="vol">{gb}</td></tr>')
    return rows

def summary(rows):
    out=""
    for label,tp,pr,ch,ytd in rows:
        out+=(f'<tr><td class="lead">{label}</td><td class="fig">{tp}</td><td class="fig">{pr}</td>'
              f'<td class="fig chg-pos">{ch}</td><td class="fig">{ytd}</td></tr>')
    return out

def chips(cs):
    return "".join(f'<span class="chip">{c}</span>' for c in cs)

def bench(rows):
    out=""
    for metric,verdict,yw,yv,aw,av in rows:
        out+=(f'<div class="bench-row"><div class="bench-label"><span class="metric">{metric}</span>'
              f'<span class="verdict">{verdict}</span></div>'
              f'<div class="bar you" style="width:{yw}%"><span class="tag">You</span><span class="val">{yv}</span></div>'
              f'<div class="bar avg" style="width:{aw}%"><span class="tag">Peer avg</span><span class="val">{av}</span></div></div>')
    return out

def handled_block(items):
    out=""
    for when,what,who in items:
        out+=(f'<div class="hx"><div class="when">{when}</div>'
              f'<div class="what">{what}<div class="who">{who}</div></div></div>')
    return f'<div class="handled">{out}</div>'

def suggestions_block(cfg):
    if "affirmation" in cfg:
        a=cfg["affirmation"]
        return (f'<div class="affirm"><div class="ic">{a["ic"]}</div><div>'
                f'<div class="t">{a["t"]}</div><div class="d">{a["d"]}</div></div></div>')
    items=""
    for ic,q,r,ask in cfg["suggestions"]:
        items+=(f'<div class="sg"><div class="ic">{ic}</div><div><div class="q">{q}</div>'
                f'<div class="r">{r}</div><div class="ask">{ask}</div></div></div>')
    return f'<div class="suggest">{items}</div>'

STYLE = open(os.path.join(HERE,'style.css')).read()

def build(cfg):
    qr_live = qr(cfg["live_url"]); qr_stmt = qr(cfg["stmt_url"]); qr_conn = qr(cfg["conn_url"])
    sug_note = "what we'd gently suggest this month" if "suggestions" in cfg else "our read this month"
    html = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A777ance — Network Activity Statement — {cfg["holder"]}</title>
<style>{STYLE}</style></head><body><div class="page">
  <div class="header"><div class="header-top">
      <div class="brandwrap"><div class="monogram"><span>A7</span></div>
        <div><div class="brand">A777ANCE</div><div class="brand-sub">Residential Network Services</div></div></div>
      <div class="doc-title"><div class="label">Network Activity Statement</div>
        <div class="period">{cfg["period"]}</div></div></div>
    <div class="acct-bar">
      <div class="acct-field"><div class="k">Account Holder</div><div class="v">{cfg["holder"]}</div></div>
      <div class="acct-field"><div class="k">Service Node</div><div class="v">HP t630</div></div>
      <div class="acct-field"><div class="k">Account No.</div><div class="v">{cfg["acct"]}</div></div>
      <div class="acct-field"><div class="k">Statement Date</div><div class="v">{cfg["stmt_date"]}</div></div></div></div>
  <div class="body">
    <div class="section"><div class="section-head"><div class="section-title">Account Summary</div>
      <div class="section-note">All figures for the statement period</div></div>
      <table class="summary"><thead><tr><th class="lead">Activity</th><th>This Period</th><th>Prior Period</th><th>Change</th><th>Year to Date</th></tr></thead>
      <tbody>{summary(cfg["summary"])}</tbody></table></div>

    <div class="section"><div class="section-head"><div class="section-title">Handled For You This Month</div>
      <div class="section-note">work done on your behalf — usually before you noticed</div></div>
      {handled_block(cfg["handled"])}
      <div class="handled-foot">{cfg["handled_foot"]}</div></div>

    <div class="section"><div class="section-head"><div class="section-title">Traffic Allocation</div>
      <div class="section-note">{cfg["total_gb"]} GB total · by category</div></div>
      <div class="alloc"><div class="donut-wrap"><div class="donut" style="{conic(cfg["alloc"])}"></div>
        <div class="donut-center"><div class="big">{cfg["total_gb"]}<span style="font-size:13px"> GB</span></div>
          <div class="lbl">Total Volume</div></div></div>
        <table class="legend">{legend(cfg["alloc"])}</table></div></div>

    <div class="section"><div class="section-head"><div class="section-title">Your Household Profile</div>
      <div class="section-note">your network's "macros" this month</div></div>
      <div class="profile"><div class="profile-badge"><div class="emoji">{cfg["emoji"]}</div>
        <div class="of">Profile of the Month</div></div>
        <div><div class="profile-name">{cfg["arch_name"]}</div><div class="profile-tag">{cfg["arch_tag"]}</div>
          <div class="profile-body">{cfg["arch_body"]}</div>
          <div class="chips">{chips(cfg["chips"])}</div>
          <div class="macro-line">{cfg["macro_line"]}</div></div></div></div>

    <div class="section"><div class="section-head"><div class="section-title">How You Compare</div>
      <div class="section-note">vs. similar households — {cfg["cohort"]}</div></div>
      {bench(cfg["bench"])}</div>

    <div class="section"><div class="section-head"><div class="section-title">{cfg["sug_title"]}</div>
      <div class="section-note">{sug_note}</div></div>
      {suggestions_block(cfg)}</div>

    <div class="section"><div class="section-head"><div class="section-title">Connect in the Alliance</div>
      <div class="section-note">optional · always opt-in</div></div>
      <div class="ally-intro">{cfg["ally_intro"]}</div>
      <div class="ally-card"><div class="avatar">{AVATAR}</div>
        <div><div class="ally-name">{cfg["ally_name"]}</div><div class="ally-role">{cfg["ally_role"]}</div>
          <div class="ally-loc">{cfg["ally_loc"]}</div><div class="ally-blurb">{cfg["ally_blurb"]}</div>
          <span class="ally-match">Matched to: {cfg["arch_name"]}</span></div>
        <div class="ally-qr"><div class="frame">{qr_conn}</div><div class="cap">Scan to connect</div></div></div>
      <div class="ally-opt">Prefer to keep to yourself? The Alliance directory is opt-in — you'll only ever appear, or be matched, if you choose to.</div></div>

    <div class="section"><div class="section-head"><div class="section-title">See For Yourself</div>
      <div class="section-note">scan with your phone camera</div></div>
      <div class="live"><div class="tile"><div class="qr-frame">{qr_live}</div>
        <div class="tile-text"><div class="t">Live network status</div>
          <div class="d">Your real-time dashboard — uptime, response time, and service health, updated to the minute.</div>
          <div class="lock">&#128274; Private to your account</div></div></div>
        <div class="tile"><div class="qr-frame">{qr_stmt}</div>
        <div class="tile-text"><div class="t">This statement, online</div>
          <div class="d">The full digital version of this report, with month-by-month history you can scroll back through.</div>
          <div class="lock">&#128274; Password protected</div></div></div></div></div>

    <div class="section"><div class="section-head"><div class="section-title">Service Status</div>
      <div class="section-note">all systems verified through statement close</div></div>
      <div class="status-grid">
        <div class="status-item"><span class="status-dot"></span>DNS filtering active</div>
        <div class="status-item"><span class="status-dot"></span>DNS queries encrypted</div>
        <div class="status-item"><span class="status-dot"></span>DNSSEC validation on</div>
        <div class="status-item"><span class="status-dot"></span>VPN tunnel healthy</div>
        <div class="status-item"><span class="status-dot"></span>Firewall — no incidents</div>
        <div class="status-item"><span class="status-dot"></span>Traffic shaping active</div></div>
      <div class="privacy"><strong>A note on privacy.</strong> Individual websites and domains are never logged, stored, or reported. The categories, profile, and suggestions above are derived from aggregate volume by type only — counted in real time and discarded. Your network appliance runs entirely within your home; no browsing data is sent to A777ance or any third party.</div></div>
  </div>
  <div class="footer"><div class="fb">A777ANCE</div>
    <div>Managed on-premises · HP t630 appliance · Account {cfg["acct"]} &nbsp;·&nbsp; <a href="mailto:hello@a777ance.com">hello@a777ance.com</a> · (555) 000-0000</div></div>
</div></body></html>'''
    return html

# ───────── ARCHETYPE CONFIGS ─────────
ARCHES = {
"prime-time": dict(
  holder="David Allum", acct="A77-001", period="Statement Period: May 1 – May 31, 2026", stmt_date="June 1, 2026",
  live_url="https://status.a777ance.com/allum", stmt_url="https://my.a777ance.com/A77-001", conn_url="https://alliance.a777ance.com/connect/m-reyes",
  handled=[("May 17","Cloudflare pushed a security update to its encrypted-DNS service. <b>Your appliance was updated the same day</b> — your private lookups kept flowing, a little faster than before.","Patched on your t630 by <span class='nm'>Jose</span>"),
           ("May 14","When Spectrum changed its routing, <b>your home's DNS was re-pointed in minutes</b> — the movie you were streaming never skipped.","Done on your line by <span class='nm'>Jose</span> · you never noticed"),
           ("May 28","<b>Your living-room smart-TV</b> hung on a bad connection; it was cleared remotely at 11:40 pm.","Fixed in your home by <span class='nm'>Jose</span> · while you slept")],
  handled_foot="Three things happened to your home this month. You felt none of them — that's the point.",
  summary=[("Queries resolved","52,441","48,902","+7.2%","251,330"),("Threats &amp; trackers blocked","9,847","8,123","+21.2%","47,221"),
           ("Protection rate","18.8%","16.6%","+2.2 pts","18.1%"),("Network availability","99.9%","99.7%","+0.2 pts","99.8%"),
           ("Peak loaded latency","12 ms","14 ms","&minus;2 ms","13 ms"),("Secure VPN sessions","14","9","+5","68")],
  total_gb="487",
  alloc=[("Streaming &amp; Video",41,"199.7 GB"),("Social &amp; Messaging",18,"87.7 GB"),("Cloud &amp; Backups",14,"68.2 GB"),
         ("Gaming &amp; Downloads",11,"53.6 GB"),("Smart Home / IoT",8,"39.0 GB"),("Shopping &amp; Web",5,"24.4 GB"),("Other",3,"14.4 GB")],
  emoji="&#127909;", arch_name="The Prime-Time Household", arch_tag="built around the evening screen",
  arch_body='Streaming led your month at <b>41%</b> of all traffic — your largest "macro" by a wide margin, with social a distant second. A classic evening-and-weekend rhythm: quiet daytime, lively nights. Gaming held steady at 11%, and your smart-home devices kept a low, constant hum in the background.',
  chips=["&#127902; <b>Screen-forward</b>","&#127769; Evening-peaked","&#127918; Steady gamer","&#127968; Always-on IoT"],
  macro_line='Think of these as your network\'s macros — like a diet, it\'s the <b>balance</b> that defines the month. Vs. April you shifted <b>+4 pts</b> toward gaming and eased off social.',
  cohort="suburban, 4–6 devices",
  bench=[("Daily data volume","18% above peer average",78,"15.7 GB/day",66,"13.3 GB/day"),
         ("Streaming share of traffic","below peer average",62,"41%",72,"48%"),
         ("Threats blocked per day","57% more — protection working harder",84,"330",53,"210"),
         ("Responsiveness under load","far better than unmanaged homes",8,"12ms",90,"~800 ms")],
  sug_title="Have You Tried?",
  suggestions=[("&#128225;","Have you tried a second Wi-Fi point near the living room?","Your 4K streaming concentrates in one room on weeknights. A mesh node there would smooth playback when several screens are on at once.","Ask us &rarr; we keep a couple on hand"),
               ("&#127909;","Have you considered a streaming-priority tuning?","We can weight your traffic shaping so video never competes with a backup or a big download after 7pm — no buffering during movie night.","Ask us &rarr; a 5-minute change, no cost"),
               ("&#9203;","Have you set up per-device downtime?","Your profile shows steady late-evening gaming. Gentle per-device schedules are easy to add if you'd ever want them — and just as easy to remove.","Ask us &rarr; or self-serve in your portal")],
  ally_intro="Your A777ance membership is also a network of people. Based on your household profile, we think you'd hit it off with a member who knows exactly the setup you're running:",
  ally_name="Marco Reyes", ally_role="Home-theater &amp; media specialist", ally_loc="A777ance member · 2.3 miles away",
  ally_blurb="&ldquo;I'm really good at home-theater calibration, mesh Wi-Fi layouts, and dialing in Plex. Would love to connect.&rdquo;"),

"home-office": dict(
  holder="Sarah Chen", acct="A77-014", period="Statement Period: May 1 – May 31, 2026", stmt_date="June 1, 2026",
  live_url="https://status.a777ance.com/chen", stmt_url="https://my.a777ance.com/A77-014", conn_url="https://alliance.a777ance.com/connect/p-nair",
  handled=[("May 11","A flaw turned up in a widely-used router service this month. <b>Your appliance was checked and hardened the same morning</b> — your home was never exposed.","Patched on your t630 by <span class='nm'>Jose</span> · before the news broke"),
           ("May 3","Ahead of your launch week, <b>your video calls were pinned to top priority on your line</b> — not one dropped call since.","Set up on your network by <span class='nm'>Jose</span> · at your request"),
           ("May 19","<b>The power adapter on your appliance</b> was reading flaky; it was swapped before it could fail and take your home office down.","Replaced in your home by <span class='nm'>Jose</span> · caught early")],
  handled_foot="Your connection is your livelihood. We watch your home like it's ours.",
  summary=[("Queries resolved","61,930","58,400","+6.0%","298,110"),("Threats &amp; trackers blocked","11,204","10,880","+3.0%","53,470"),
           ("Protection rate","18.1%","18.6%","&minus;0.5 pts","18.4%"),("Network availability","99.99%","99.9%","+0.09 pts","99.96%"),
           ("Peak loaded latency","9 ms","11 ms","&minus;2 ms","10 ms"),("Secure VPN sessions","42","38","+4","214")],
  total_gb="612",
  alloc=[("Cloud &amp; Backups",27,"165.2 GB"),("Video Conferencing",22,"134.6 GB"),("Streaming &amp; Video",17,"104.0 GB"),
         ("Web &amp; SaaS",14,"85.7 GB"),("Social &amp; Messaging",11,"67.3 GB"),("Smart Home / IoT",6,"36.7 GB"),("Other",3,"18.5 GB")],
  emoji="&#128188;", arch_name="The Home Office", arch_tag="the network clocks in at 9 a.m.",
  arch_body='Your traffic peaks in the <b>workday</b>, not the evening — cloud sync and video calls together made up <b>49%</b> of the month. Uptime and upload stability matter more here than raw volume: a dropped second on a call costs more than a slow movie. Your network delivered, holding sub-10ms latency through the busiest hours.',
  chips=["&#9728; <b>Daytime-peaked</b>","&#128222; Call-heavy","&#9729; Cloud-reliant","&#11014; Upload-sensitive"],
  macro_line='These macros say "professional, not playful." Vs. April, video conferencing rose <b>+3 pts</b> as cloud backups held flat — a busier month of calls.',
  cohort="home-based workers, 3–5 devices",
  bench=[("Workday data volume","31% above peer average",82,"24.1 GB/day",58,"18.4 GB/day"),
         ("Video-call share of traffic","well above peer average",80,"22%",48,"13%"),
         ("Uptime during 9–5","best-in-class — zero call drops",96,"99.99%",72,"99.7%"),
         ("Upload responsiveness","calls stay crisp under load",90,"9ms",30,"~300 ms")],
  sug_title="Have You Tried?",
  suggestions=[("&#128267;","Have you considered a battery backup (UPS)?","Your livelihood runs over this connection. A small UPS keeps the appliance and router alive through brief outages — so a flickering power line never drops you mid-call.","Ask us &rarr; we can spec one to your gear"),
               ("&#128249;","Have you tried locking video calls to top priority?","We can pin conferencing above everything in your traffic shaping, so a cloud backup kicking off never steals from a live Zoom.","Ask us &rarr; a 5-minute change, no cost"),
               ("&#128268;","Have you thought about a wired link to your desk?","All-day calls are happiest off Wi-Fi. If your desk is near the appliance, a single cable removes wireless jitter entirely.","Ask us &rarr; we'll check the run")],
  ally_intro="Your A777ance membership is also a network of people. Based on your household profile, we think you'd hit it off with a member who lives the work-from-home setup too:",
  ally_name="Priya Nair", ally_role="Remote-work network specialist", ally_loc="A777ance member · 1.1 miles away",
  ally_blurb="&ldquo;I set up rock-solid home offices — UPS, wired backhaul, call-priority QoS. Happy to compare notes anytime.&rdquo;"),

"connected-family": dict(
  holder="The Okafor Family", acct="A77-008", period="Statement Period: May 1 – May 31, 2026", stmt_date="June 1, 2026",
  live_url="https://status.a777ance.com/okafor", stmt_url="https://my.a777ance.com/A77-008", conn_url="https://alliance.a777ance.com/connect/t-bishop",
  handled=[("May 8","Pi-hole shipped a filtering upgrade. <b>Your home's blocklists were updated the same day</b> — all 18 devices, in one sweep.","Patched on your t630 by <span class='nm'>Jose</span>"),
           ("May 9","<b>A smart-plug in your home</b> started flooding the network with chatter; it was isolated before anyone felt a lag.","Diagnosed in your home by <span class='nm'>Jose</span>"),
           ("May 12","<b>Two new devices</b> — a tablet and a console — were added to your secure network, no setup needed from you.","Onboarded in your home by <span class='nm'>Jose</span>")],
  handled_foot="A busy house, kept quiet. Eighteen devices, one calm network — and someone watching it.",
  summary=[("Queries resolved","88,260","90,140","&minus;2.1%","441,300"),("Threats &amp; trackers blocked","17,540","16,990","+3.2%","84,120"),
           ("Protection rate","19.9%","18.8%","+1.1 pts","19.1%"),("Network availability","99.95%","99.9%","+0.05 pts","99.93%"),
           ("Peak loaded latency","14 ms","16 ms","&minus;2 ms","15 ms"),("Secure VPN sessions","21","19","+2","96")],
  total_gb="934",
  alloc=[("Streaming &amp; Video",30,"280.2 GB"),("Smart Home / IoT",20,"186.8 GB"),("Gaming &amp; Downloads",16,"149.4 GB"),
         ("Social &amp; Messaging",14,"130.8 GB"),("Cloud &amp; Backups",10,"93.4 GB"),("Shopping &amp; Web",6,"56.0 GB"),("Other",4,"37.4 GB")],
  emoji="&#128106;", arch_name="The Connected Family", arch_tag="many devices, one happy network",
  arch_body='With <b>18 devices</b> under one roof — phones, tablets, consoles, and a small army of smart-home gadgets — yours is one of the busiest networks we manage. Smart Home / IoT alone was 20% of traffic. And yet it stayed fast and tidy all month: no congestion, no slowdowns, even on weekend evenings when everything is on at once.',
  chips=["&#128241; <b>Device-dense (18)</b>","&#128126; IoT-heavy","&#128118; Family hours","&#127777; Weekend-peaked"],
  macro_line='A wonderfully balanced spread — no single macro dominates, which is exactly what you want in a full house. Vs. April, volume eased <b>2%</b> even as device count grew.',
  cohort="large families, 12+ devices",
  bench=[("Total monthly volume","2.0× the peer average",92,"934 GB",46,"470 GB"),
         ("Devices on the network","among the most we manage",90,"18",45,"9"),
         ("Threats blocked per day","keeping a big household clean",88,"566",50,"320"),
         ("Responsiveness under load","steady despite the crowd",16,"14ms",90,"~800 ms")],
  sug_title="Our Read This Month",
  affirmation=dict(ic="&#9989;", t="Nothing to change this month.",
    d="We looked hard — with 18 devices and nearly a terabyte of traffic, your network stayed fast, filtered, and congestion-free all month. There's genuinely nothing we'd tune right now. Beautifully boring. We'll keep watching."),
  ally_intro="Your A777ance membership is also a network of people. Based on your household profile, we think you'd hit it off with a member who runs a busy, device-dense home like yours:",
  ally_name="Tom Bishop", ally_role="Smart-home &amp; multi-device specialist", ally_loc="A777ance member · 3.0 miles away",
  ally_blurb="&ldquo;I wrangle big smart-home setups — VLANs for IoT, guest networks, parental schedules. Always glad to swap tips.&rdquo;"),
}

import os
out_dir=os.path.join(HERE,"..","client")
os.makedirs(out_dir, exist_ok=True)
names={"prime-time":"archetype-prime-time.html","home-office":"archetype-home-office.html","connected-family":"archetype-connected-family.html"}
for key,cfg in ARCHES.items():
    html=build(cfg)
    open(os.path.join(out_dir,names[key]),"w").write(html)
    print("wrote",names[key],len(html),"bytes")
