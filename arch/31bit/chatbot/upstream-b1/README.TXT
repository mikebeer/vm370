CHATBOT  build 1  -  the MCchat persona bot as a VM/370 service machine
=========================================================================

What it is
  The Godot bot (autoloads/bot.gd, NPC chat of MCchat) ported to cREXX.
  It runs as its own CMS guest, CHATBOT.  Users punch a question to it
  (PUNCH to its reader); CHATBOT reads its RDR, answers, and punches the
  answer (PUN) back to the sender's reader.  No model, no network: every
  answer is authored text from the persona data, picked the same way the
  Godot bot picks it.  The 10 personas x EN/DE and the 480 KB knowledge
  base of the MCchat bundle are the demo data.

Contents of this kit
  README.TXT          this manual
  src/chatbot.crexx   the bot (Level B cREXX), about 1600 lines
  bin/chatbot.rxbin   compiled on the PC (ASCII) - see "Installing"
  cms/                CHATBOT EXEC, CHAT EXEC, PROFILE EXEC, CHATBOT CONFIG,
                      CHATBOT DIRECT (directory entry sample)
  data/               40 persona files + CHATKB DATA + CHATDATA LIST
                      (80-column records, ASCII, ready to load)
  deck/               CHATBOT.DECK  all text files as one :READ card deck
  tools/              mkdata.py (MCchat data -> data/), mkdeck.py
  tests/              PC tests: spool simulation, cross-check vs. a Python
                      reference of bot.gd, KB check, selftest.sh
  demo/SESSION.TXT    a sample conversation (output of the simulation)

How it talks (the spool protocol)
  Client (CHAT EXEC):  FROM userid
                       question text            -> PUNCH ... (NOHEADER)
  CHATBOT EXEC:   QUERY READER ALL -> ORIGINID of the next file
                  READCARD Qnnnn CBREQ A (NOHEADER    one file per question
                  first card is rewritten to  FROM <ORIGINID>
                  after the reader is empty (or MAXBATCH reached):
                  CHATBOT CBQUEUE lists the Qnnnn names, RXVM CHATBOT CMS
                  runs once for all of them and writes Qnnnn CBRPL
                  SPOOL PUNCH TO <sender>, PUNCH Qnnnn CBRPL, CLOSE PUNCH
                  (file name CHATBOT REPLY)
  The sender is always the ORIGINID of the spool file - nobody can ask
  for somebody else's answers.  Conversation state (persona, language,
  last topic, script position) is kept per sender in  <USERID> CBSESS A.

Using it
  CHAT how are you today            one question, the answer is typed
  CHAT                              talk; empty line ends
  CHAT (WAIT 120 LOUD
  Or by hand:  a file with the two lines  FROM userid / question,
  PUNCH fn ft A (NOHEADER after  CP SPOOL PUNCH TO CHATBOT ,
  later READCARD the reply.
  Commands (start with /):  /HELP  /LIST  /NPC name [en|de]  /LANG en|de
                            /RESET  /WHO  /DEBUG ON|OFF
  Personas: amicus andron elena galene hord mcjoy musix opux spark
            tchaika, each en and de.  Default persona: CHATBOT CONFIG.

Installing on the VM/370 system
  1. Directory: add the CHATBOT entry (cms/CHATBOT.DIRECT).  It must have
     OPTION ECMODE, a reader/punch, a 191 disk with ~3 MB free (the data
     is 2 MB), and LINKs to the system disks.  Format the 191.
  2. Log on as CHATBOT, ACCESS 191 A.  Send deck/CHATBOT.DECK to the
     CHATBOT reader (it holds :READ cards) and load it:
        READCARD  (repeat until the reader is empty)
     This creates the EXECs, CHATBOT CONFIG and all persona files.
  3. The compiled bot is binary: put bin/chatbot.rxbin on the 191 as
     CHATBOT RXBIN with the same tool you use for the other cREXX
     programs (the PC build is ASCII; convert/translate exactly as you
     do for your own RXBINs).  Alternatively compile src/chatbot.crexx
     with the cREXX of the VM/370 system (RXC / RXAS) - the source uses
     only plain Level B (no classes, no ADDRESS).
  4. Start:   EXEC CHATBOT (LOUD       and watch one test question.
     Autostart: PROFILE EXEC already ends in EXEC CHATBOT; XAUTOLOG
     CHATBOT from the system start-up.
  5. From a user:  CHAT hello
  Stop: create CHATBOT STOP A on the 191 (the loop ends at its next
  check), or FORCE CHATBOT.

Options (EXEC options go after the "(" ; quiet is the default)
  CHATBOT (LOUD  ONCE  INTERVAL n)
  CHATBOT CONFIG keys: DEFNPC DEFLANG WIDTH CRISIS BOTCMD MAXBATCH
  INTERVAL SEED VAR name value.

What was ported - and what was left out
  Ported, and cross-checked against a line-by-line Python translation of
  bot.gd on 3000 generated messages plus 800 for the knowledge base:
  normalising, tokens, Damerau edit distance and fuzzy matching, synonym
  scoring, crisis detection, pronoun carry-over and entities,
  continuation words, repeat flag, say_template, variant choice without
  immediate repeat, [VAR] and $VAR. interpolation, the .bot script
  interpreter (labels, say, buttons, input, branches, IF/IFEMPTY, SET/LET,
  GOTO, EXIT), and the knowledge-base search.
  Left out: everything that is Godot screen: bubbles, speech in/out,
  images, audio, weather map, to-do, shards, questionnaires, the HTTPS
  backend.  Intents that only trigger such a feature answer with a short
  "that is a screen feature" line.
  Data: non-ASCII letters are folded to ASCII (ae oe ue ss ...) so that
  EBCDIC and 3270 can carry them; DE answers read "schoen", "fuehrt".

Things to know / to check on the system   (please read)
  * The CMS side (CHATBOT EXEC, CHAT EXEC, PROFILE EXEC) could not be run
    here - there is no VM/370 in the build environment.  The bot itself
    and the whole protocol are tested through a PC simulation; the EXECs
    use these CMS features whose exact behaviour on your system should be
    confirmed once: READCARD ... (NOHEADER, EXECIO ... CP (STRING (to
    capture QUERY READER ALL), CP SPOOL PUNCH TO / CLOSE PUNCH NAME,
    WAKEUP ... (RDR (falls back to a busy wait when absent), and the call
    RXVM CHATBOT CMS (change BOTCMD in CHATBOT CONFIG if yours differs).
    In the bot all file access is in three small procedures (fid,
    rd_file, wr_ob) - if RXVM names CMS files differently, that is the
    only place to change.
  * Tested with the current cREXX tree; the cREXX CMS port in the project
    is the 2022 tree.  Compile on the target once and run the same test.
  * CRISIS defaults to YES here (the Godot default is off): words from
    the persona's crisis list get the persona's care text.  Set
    CRISIS NO in CHATBOT CONFIG for the original behaviour.
  * One reader file = one question.  Keep your own reader empty while you
    use CHAT (it reads the first file there).
  * Long answers: lines are wrapped at WIDTH (72) for 3270.

PC tests
  sh tests/selftest.sh <cREXX build dir> <MCchat assets/data/npc_chat>
  (rebuilds the data and the bot, runs the cross-checks; ~2 minutes)
  Regenerate data:  python3 tools/mkdata.py <npc_chat dir> data --build 2
  Regenerate deck:  mkdir t; cp cms/* data/* t/; python3 tools/mkdeck.py t deck/CHATBOT.DECK
