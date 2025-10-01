
git clone -b MOODLE_500_STABLE https://github.com/moodle/moodle.git
( cd moodle/mod && git clone https://github.com/KQMATH/moodle-mod_capquiz.git capquiz )
( cd moodle/question/type && git clone https://github.com/trampgeek/moodle-qtype_coderunner.git coderunner )

( cd moodle/question/behaviour/ && git clone https://github.com/trampgeek/moodle-qbehaviour_adaptive_adapted_for_coderunner.git adaptive_adapted_for_coderunner )
