while [ "true" ]
do
  arch -i386 osascript skypeChecker.scpt
  python2.5 audio_analysis.py >> /var/tmp/audio.log
  sleep 2
done
