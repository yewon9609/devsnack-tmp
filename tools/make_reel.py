#!/usr/bin/env python3
"""Join the card videos into one 9:16 Reel.
Usage: python3 tools/make_reel.py OUT_DIR  -> OUT_DIR/reel.mp4 (1080x1920, cards centered on the dark background)"""
import pathlib, subprocess, sys
out = pathlib.Path(sys.argv[1]).resolve()
vids = sorted(out.glob('devsnack_[0-9][0-9].mp4'))
if not vids: sys.exit('no card videos')
lst = out / '_reel.txt'
# cover and outro play once; content cards play twice so there is time to read them
lst.write_text(''.join(f"file '{v}'\n" * (1 if i in (0, len(vids) - 1) else 2) for i, v in enumerate(vids)))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(lst),
                '-vf', 'pad=1080:1920:0:285:color=0x121110,format=yuv420p', '-r', '30',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-c:a', 'aac', '-b:a', '64k',
                '-movflags', '+faststart', str(out / 'reel.mp4')], check=True)
lst.unlink()
print(out / 'reel.mp4')
