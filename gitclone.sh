

git clone -b MOODLE_500_STABLE https://github.com/moodle/moodle.git

mkdir -p moodle/mod
mkdir -p moodle/question/type
mkdir -p moodle/question/behaviour

( cd moodle/mod && git clone https://github.com/KQMATH/moodle-mod_capquiz.git capquiz )
( cd moodle/question/type && git clone https://github.com/trampgeek/moodle-qtype_coderunner.git coderunner )
( cd moodle/question/type && git clone https://github.com/maths/moodle-qtype_stack.git stack )

( cd moodle/question/behaviour/ && \
  git clone https://github.com/maths/moodle-qbehaviour_dfexplicitvaildate.git dfexplicitvaildate && \
  git clone https://github.com/maths/moodle-qbehaviour_dfcbmexplicitvaildate.git dfcbmexplicitvaildate && \
  git clone https://github.com/maths/moodle-qbehaviour_adaptivemultipart.git adaptivemultipart )


( cd moodle/question/behaviour/ && git clone https://github.com/trampgeek/moodle-qbehaviour_adaptive_adapted_for_coderunner.git adaptive_adapted_for_coderunner )
