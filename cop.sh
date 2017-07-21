#!/bin/bash

verbose=0
base_directory=$(git rev-parse --show-toplevel)
current_directory=$(pwd)
branch=$(git rev-parse --abbrev-ref HEAD)
npm_folder='app_client'
public_folder='app_client'
info_ok="👌 "
info_fail="🔥 "
isort='isort -sp ./.isort.cfg '
status_ok="👍 "
status_fail="💥 "
html_hint_exec='./app_client/node_modules/gulp-htmlhint/node_modules/htmlhint/bin/htmlhint --config app_client/.htmlhintrc'

# Back to current folder on end
trap "cd ${current_directory}" SIGINT SIGTERM EXIT
cd "${base_directory}"

# Override default execs, variables, etc...
if [ -f "local.sh" ]; then
  source "local.sh"
fi

# Load files exceptions (only for HTML now)
if [ -f "file_exceptions.sh" ]; then
  source "file_exceptions.sh"
fi

info () {
  show=verbose
  if [ -n "$4" ]; then
    show=$4
  fi
  if [ "${1}" -eq '0' ]; then
    if [ $show -eq 1 ] ; then
      printf '%b %b\n' "${info_ok}" "${2}" >&2
    fi
  else
    printf '%b %b\n' "${info_fail}" "${2}" >&2
    if [ -z $3 ] || [ $3 -eq 1 ] ; then
      exit 1
    fi
  fi
}

program_exists () {
  local ret='0'
  type $1 >/dev/null 2>&1 || { local ret='1'; }
  # throw error on non-zero return value
  if [ ! "${ret}" -eq '0' ]; then
    info 1 "Sorry, we cannot continue without ${1}, please install it first. ${2}" $3
  fi
}

containsElement () {
  local e
  for e in "${@:2}"; do [[ "$e" == "$1" ]] && return 0; done
  return 1
}

###############################################################################
# INSTALL
###############################################################################

install () {
  cat > .git/hooks/pre-commit << 'EOF'
base_directory=$(git rev-parse --show-toplevel)
eval "${base_directory}/cop.sh pre-commit --verbose HEAD"
EOF
  chmod +x .git/hooks/pre-commit
  info 0 "The pre-commit hook was installed." 0 $1

  cat > .git/hooks/commit-msg << 'EOF'
base_directory=$(git rev-parse --show-toplevel)
eval "${base_directory}/cop.sh commit-msg $@"
EOF
  chmod +x .git/hooks/commit-msg
  info 0 "The commit-msg hook was installed." 0 $1
}



###############################################################################
# PRE COMMIT
###############################################################################

function pre_commit () {

  # Execs
  if [ -z "${eslint_exec}" ]; then
    eslint_exec="npm run eslint --"
  fi

  # Protected branches:
  if [[ "$branch" == "master" || "$branch" == "dev" ]]; then
    printf "🔥  \e[31mYou CAN'T commit on branch ${branch}.\e[0m\n"
    exit 1
  fi

  check_py=1
  check_py_lint=0
  check_scss=1
  check_scss_lint=1
  check_js=1
  check_js_lint=1
  check_html=1
  check_images=1

  verbose=0
  exit_on_error=1

  while [ $# -gt 0 ]
  do
    case "$1" in

    --verbose)
      verbose=1
      shift
    ;;

    --no-exit)
      exit_on_error=0
      shift
    ;;

    --py)
      check_py=1
      shift
    ;;

    --no-py)
      check_py=0
      shift
    ;;

    --py-lint)
      check_py_lint=1
      shift
    ;;

    --no-py-lint)
      check_py_lint=1
      shift
    ;;

    --no-scss)
      check_scss=0
      shift
    ;;

    --no-scss-lint)
      check_scss_lint=0
      shift
    ;;

    --js)
      check_js=1
      shift
    ;;

    --no-js)
      check_js=0
      shift
    ;;

    --no-js-lint)
      check_js_lint=0
      shift
    ;;

    --html)
      check_html=1
      shift
    ;;

    --no-html)
      check_html=0
      shift
    ;;

    --images)
      check_images=1
      shift
    ;;

    --no-images)
      check_images=0
      shift
    ;;

    -*)
      echo "Invalid option: ${1}"
      exit 1
    ;;

    *)
      target=$1
      shift
    ;;
    esac
  done

  ignore=(
    '^_trash'
    '^docs'
    '^keys'
    'api\.js$'
    '^extras'
    'api\.js$'
    '^app/.*/migrations/'
    '^app/.*/vendor/'
  )
  exclude=`python -c 'import sys;print("({})".format("|".join(sys.argv[1:])))' "${ignore[@]}"`

  # List files
  if [[ -n $target ]]; then
    if [[ $target =~ ^([0-9abcdef]{7,40})$ ]]; then
      files=`git show --pretty="format:" --name-only ${target} | grep -Ev ${exclude}`
    elif [[ $target =~ ^(HEAD)$ ]]; then
      files=`git diff --cached --name-only --diff-filter=AMR ${target} | grep -Ev ${exclude}`
    elif [[ $target =~ ^\.$ ]]; then
      files=`git ls-files| grep -Ev ${exclude}`
    else
      if [ ! -f $target ]; then
        echo "File not found: ${target}"
        exit 1
      fi
      files=$target
    fi
  else
    files=`git status --porcelain -uall | awk 'match($1, /R|RM/) {print $4; next} match($1, /A|M|MM|AM/) {print $2}' | grep -Ev ${exclude}`
  fi

  result=0

  status () {
    if [ "${3}" -eq '0' ]; then
      if [ $verbose -eq 1 ] || [ -n "${4}" ] ; then
        # printf "\e[32m  ${2}\e[0m%b\n" >&2
        printf "${status_ok} \e[32m${2}\e[0m%b: ${1}\n" >&2
      fi
    else
      # printf "  \e[31m❯ ${2}\e[0m%b\n" >&2
      printf "${status_fail} \e[31m${2}\e[0m%b: ${1}\n" >&2
      result=1
      if [ -z $exit_on_error ] || [ $exit_on_error -eq 1 ] ; then
        exit 1
      fi
    fi
  }


  # For each file...
  for file in $files; do
    if containsElement $file "${FILE_EXCEPTIONS[@]}"; then
      continue
    fi

    if [ ! -f $file ]; then
      continue
    fi

    # unresolved merge conflict
    cat "${file}" |  grep -n -E "(^<<<<<<<\s|^=======\$|^>>>>>>>\s)" | grep -v "noqa"
    if [ $? -eq 0 ]; then
      status $file 'git-conflict' 1
    else
      status $file 'git-conflict' 0
    fi

    contains_super=`cat $file | grep '\ssuper([a-zA-Z]\+)'`;
    if [[ ! -z $contains_super ]]; then
        status $file 'contains-super-with-params' 1
        exit 1;
    fi

    # python
    if [ $check_py -eq 1 ] ; then
      if [[ $file =~ \.py$ ]]; then
        program_exists 'flake8' '(pip install flake8)'
        program_exists 'isort' '(pip install isort)'
        program_exists 'pylint' '(pip install pylint)'

        # filename format
        if [[ $file =~ (^|/)[a-z_0-9]+\.py$ ]] ; then
          status $file 'py-ff' 0
        else
          echo "Invalid filename format: {$file}"
          status $file 'py-ff' 1
        fi

        # isort
        ${isort} -ns __init__.py --check-only "${file}"
        if [ $? -eq '0' ]; then
          status $file 'py-isort' $?
        elif [[ $target =~ ^(HEAD)$ ]]; then
          ${isort} -ns __init__.py "${file}"
          ${isort} -ns __init__.py --check-only "${file}"
          git add "${file}"
          status $file 'py-isort-autofix' $? 1
        else
          status $file 'py-isort' $?
        fi

        # flake8
        flake8 "${file}"
        status $file 'py-flake8' $?

        # pylint
        if [ $check_py_lint -eq 1 ] ; then
            pylint --rcfile="${base_directory}/.pylintrc" "${file}"
            status $file 'py-pylint' $?
        fi

        # i18n_deprecated
        cat "${file}" |  grep -o -n -E "gettext"
        if [ $? -eq 0 ]; then
          status $file 'py-i18n' 1
        else
          status $file 'py-i18n' 0
        fi

        # forgotten_prints
        noqa=`cat "${file}" | grep "noqa: print"`
        if [ $? -eq 1 ]; then
          cat "${file}" | grep -n -E "\bprint\s*\(" | grep -v "noqa"
          if [ $? -eq 0 ]; then
            status $file 'py-fp' 1
          else
            status $file 'py-fp' 0
          fi
        fi

        # forgotten_debbug_lines
        noqa=`cat "${file}" | grep "noqa: debug"`
        if [ $? -eq 1 ]; then
          cat "${file}" | grep -n -E "\bset_trace\s*\(" | grep -v "noqa"
          if [ $? -eq 0 ]; then
            status $file 'py-fd' 1
          else
            status $file 'py-fd' 0
          fi
        fi
      fi
    fi



    # scss
    if [ $check_scss -eq 1 ] ; then
      if [[ $file =~ \.scss$ ]]; then
        program_exists 'scss-lint' '(gem install scss-lint)'

        # scss: filename format
        if [[ $file =~ (^|/)_?[a-z0-9\-]+\.scss$ ]] ; then
          status $file 'scss-ff' 0
        else
          echo "Invalid filename format: {$file}"
          status $file 'scss-ff' 1
        fi

# FIXME: Disabled, because is intented to be used with a prefixer
#        cat "${file}" | grep -v "\b@mixin cross-browser\b" | grep -o -n -E "\bcross-browser\b"
#        if [ $? -eq 0 ]; then
#          status $file 'scss-cb' 1
#        else
#          status $file 'scss-cb' 0
#        fi
#
#        cat "${file}" | grep -o -n -E "\bcrossBrowser\b"
#        if [ $? -eq 0 ]; then
#          status $file 'scss-cb' 1
#        else
#          status $file 'scss-cb' 0
#        fi

        # scss-lint
        if [ $check_scss_lint -eq 1 ] ; then
          scss-lint --require "${base_directory}/extras/scss_linters/no_pointer_events.rb" "$file"
          status $file 'scss-lint' $?
        fi
      fi
    fi


    # js
    if [ $check_js -eq 1 ] ; then
      if [[ $file =~ \.js$ ]]; then

        # filename_format
        if [[ $file =~ (^|/)[a-z0-9\.\-]+\.js$ ]] ; then
          status $file 'js-ff' 0
        else
          echo "Invalid filename format: {$file}"
          status $file 'js-ff' 1
        fi

        # forgotten_log
        cat "${file}" | grep -o -n -E "\bconsole.log\b" | grep -v "noqa"
        if [ $? -eq 0 ]; then
          status $file 'js-fl' 1
        else
          status $file 'js-fl' 0
        fi

        # forgotten debugger
        cat "${file}" | grep -o -n -E "\bdebugger\b" | grep -v "noqa"
        if [ $? -eq 0 ]; then
          status $file 'js-debug' 1
        else
          status $file 'js-debug' 0
        fi

        # eslint
        if [ $check_js_lint -eq 1 ] ; then
          cd "$npm_folder"
          eval "${eslint_exec} ${file}"
          status $file 'js-eslint' $?
          cd -
        fi

      fi
    fi


    # HTML
    if [ $check_html -eq 1 ] ; then
      if [[ $file =~ \.html$ ]]; then

        # filename format
        regex="^$public_folder/"
        if [[ $file =~ $regex ]] ; then
          if [[ $file =~ (^|/)[a-z0-9\-]+\.html$ ]] ; then
            status $file 'html-ff' 0 ''
          else
            status $file 'html-ff' 1 "${file}"
          fi
        else
          if [[ $file =~ (^|/)[a-z0-9\_]+\.html$ ]] ; then
            status $file 'html-ff' 0 ''
          else
            status $file 'html-ff' 1 "${file}"
          fi
        fi

        # blocks_name_format
        cat "${file}" |  grep -o -n -E "\{\%\s+block\s+[a-z0-9_]*[A-Z\-]+[a-z0-9_]*"
        if [ $? -eq 0 ]; then
          status $file 'html-block' 1
        else
          status $file 'html-block' 0
        fi

        # i18n_deprecated
        cat "${file}" |  grep -o -n -E "\{\%\s+load\s+i18n\s+\%\}"
        if [ $? -eq 0 ]; then
          status $file 'html-i18n' 1
        else
          status $file 'html-i18n' 0
        fi

        # trans_deprecated
        cat "${file}" |  grep -o -n -E "\{\%\s+trans\s+[^%]+"
        if [ $? -eq 0 ]; then
          status $file 'html-trans' 1
        else
          status $file 'html-trans' 0
        fi

        # htmlhint
        eval "${html_hint_exec} ${file}"
        status $file 'html-hint' $?

      fi
    fi


    # Images
    if [ $check_images -eq 1 ] ; then
      if [[ $file =~ \.(jpeg|gif|png|jpg)$ ]]; then

        status '🙏 \e[31mPLEASE: RENAME THE IMAGE FILE IF YOU MODIFIED IT.\e[0m' 'images-warn'  0

        # filename_format
        if [[ $file =~ (^|/)[a-z0-9\-]+\.(jpeg|gif|png|jpg)$ ]] ; then
          if [[ $file =~ \.(jpeg|jpg)$ ]]; then
            jpegoptim -m90 $file
          fi
          if [[ $file =~ \.(gif|png)$ ]]; then
            optipng $file
          fi
          status $file 'images-ff' 0
        else
          echo "Invalid filename format: {$file}"
          status $file 'images-ff' 1
        fi

      fi
    fi

  done

  if [ $result -eq 0 ] ; then
    echo "👮  < Move along. There's nothing to see here."
  fi

  exit $result
}

###############################################################################
# COMMIT MSG
###############################################################################

function commit_msg ()
{
	return;

# ./check_ticket.py  ${line}
# if [ $? -eq '1' ]; then
#   printf "🔥  \e[31mInvalid commit JIRA ticket: ${line}\e[0m \n"
#
#   exit 1
# fi

}


###############################################################################
# READ ARGS
###############################################################################

install 0

case "$1" in

pre-commit)
  shift
  pre_commit $@
;;

commit-msg)
  shift
  commit_msg $@
;;

install)
  shift
  install 1
;;

-*)
  pre_commit $@
;;

*)
  pre_commit $@
;;
esac
