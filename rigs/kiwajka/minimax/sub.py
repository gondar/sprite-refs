"""sub.py TAG PROMPT FIRST LAST [DUR]: h3.py submit, retried while the free media check gets a 403 (nothing billed then);
then polls in the background to raw/<job>.mp4. Run from the sprite-refs root."""
import subprocess, sys, json, time
import os
BASE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "base.txt")).read().strip()
PIC = {"home": "home-wide-blue.png", "uke": "uke-peak-wide-blue.png"}
tag, prompt, first, last = sys.argv[1:5]; first, last = BASE + "/" + PIC.get(first, first), BASE + "/" + PIC.get(last, last); dur = sys.argv[5] if len(sys.argv) > 5 else "4"
for k in range(8):
    r = subprocess.run([sys.executable, "skill/sprite-pipeline/scripts/h3.py", "submit", "--tag", tag, "--prompt-file", prompt,
                        "--duration", dur, "--ratio", "adaptive", "--first", first, "--last", last], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip().splitlines()
    line = out[-1] if out else ""
    if '"job_id"' in line:
        job = json.loads(line)["job_id"]; print(tag, job)
        subprocess.Popen([sys.executable, "skill/sprite-pipeline/scripts/h3.py", "poll", job, "--every", "15"],
                         stdout=open(f"../poll-{tag}.log", "w"), stderr=subprocess.STDOUT, start_new_session=True)
        break
    if "media check" not in line and "403" not in line: print(tag, "FAILED:", line); break
    time.sleep(3)
else:
    print(tag, "gave up on the media check")
