=============
Twitter Robot
=============


Database
========

#. Create Database and user::

    $ sudo -u postgres psql
    psql (13.4 (Debian 13.4-0+deb11u1))
    Type "help" for help.

    postgres=# create database surviral_avd;
    CREATE DATABASE
    postgres=# create user surviral_avd with encrypted password 'surviral_avd';
    CREATE ROLE
    postgres=# grant all privileges on database surviral_avd to surviral_avd;
    GRANT
    postgres=# exit

#. Export environment viriables in ``~/.bashrc``::

    export SURVIRAL_DATABASE_NAME=surviral_avd
    export SURVIRAL_DATABASE_USER=surviral_avd
    export SURVIRAL_DATABASE_PASSWORD=surviral_avd
    export DATABASE_HOST=localhost
    export DATABASE_PORT=5432

#. Create database and data for django project::

    python manage.py makemigrations core
    python manage.py migrate core

    python manage.py migrate

    python manage.py makemigrations twbot
    python manage.py migrate twbot


- django.db.utils.ProgrammingError: relation "core_user" does not exist

  ::

    $ python manage.py migrate
    Operations to perform:
      Apply all migrations: admin, auth, contenttypes, sessions
    Running migrations:
      Applying contenttypes.0001_initial... OK
      Applying admin.0001_initial...Traceback (most recent call last):
      File "/home/test/Project/Surviral/venv/lib/python3.9/site-packages/django/db/backends/utils.py", line 84, in _execute
        return self.cursor.execute(sql, params)
    psycopg2.errors.UndefinedTable: relation "core_user" does not exist

    ...

    django.db.utils.ProgrammingError: relation "core_user" does not exist


  Solution::

    ./manage.py makemigrations core
    ./manage.py migrate core
    ./manage.py migrate
    ./manage.py makemigrations twbot
    ./manage.py migrate twbot


Install & Configure
===================

CAPTCHA Configure for Android
-----------------------------

- Download `Death By Captcha API`__, then unzip and put it into the root directory
  of the project. (This folder has existed in repository)

  __ https://static.deathbycaptcha.com/files/dbc_api_v4_6_3_python3.zip

- Install ``Pillow``::

    pip install --upgrade Pillow

  Or::

    pip install -r requirements.txt

- Configure some options in the file ``conf.py``::

    # captcha
    RECAPTCHA_ALL_RETRY_TIMES = 15  # the number of captcha images to resolve
    FUNCAPTCHA_ALL_RETRY_TIMES = 20  # the number of captcha images to resolve
    CAPTCHA_IMAGE_DIR_NAME = 'temp'

- Import captcha API and use it::

    from verify import RecaptchaAndroidUI, FuncaptchaAndroidUI
    from conf import RECAPTCHA_ALL_RETRY_TIMES, FUNCAPTCHA_ALL_RETRY_TIMES

    # resolve reCAPTCHA
    recaptcha = RecaptchaAndroidUI(self.app_driver)
    if recaptcha.is_captcha_first_page():
        LOGGER.info('Resovling reCAPTCHA')
        if recaptcha.resolve_all_with_coordinates_api(
                all_resolve_retry_times=RECAPTCHA_ALL_RETRY_TIMES):
            LOGGER.info('reCAPTCHA is resolved')
        else:
            LOGGER.info('reCAPTCHA cannot be resolved')

    # resolve FunCaptcha
    funcaptcha = FuncaptchaAndroidUI(self.app_driver)
    if funcaptcha.is_captcha_first_page():
        LOGGER.info('Resovling FunCaptcha')
        if funcaptcha.resolve_all_with_coordinates_api(
                all_resolve_retry_times=RECAPTCHA_ALL_RETRY_TIMES):
            LOGGER.info('FunCaptcha is resolved')
        else:
            LOGGER.info('FunCaptcha cannot be resolved')

Database Configuration
----------------------

Run the command::

  $ python manage.py setup --database

Generate Action Report
----------------------

Install the lib ``openpyxl``::

  pip install openpyxl

Or::

  pip install -r requirements.txt

Run the command to generate action report::

  python manage.py generate_report

Or::

  python manage.py generate_report -f <report_file_name>

Check the report in the file ``outputs/action_report.xlsx``

Cyberghost VPN Configuration
----------------------------

Download `Cyberghost vpn apk`__ and put it into the directory ``apk``.

__ https://www.apkmirror.com/apk/cyberghost-sa/cyberghost-vpn/

Configure the path of it in the file ``conf.py``::

  # cyberghostvpn
  CYBERGHOSTVPN_APK = PACKAGES_DIR / 'cyberghostvpn_8.6.4.396.apk'

Use it through the function ``connect_to_nord_vpn``::

  if vpn_type == 'cyberghostvpn':
      LOGGER.info('Connect to CyberGhost VPN')
      vpn = CyberGhostVpn(self.driver())
      reconnect = True
      return vpn.start_ui(reconnect=reconnect)

Parallel Running
----------------

Add an option ``--parallel_number`` for the command ``auto_engage``::

  --parallel_number [PARALLEL_NUMBER]
                        Number of parallel running. Default: 2(PARALLEL_NUMER
                        in the file conf.py)

You can configure the default number in the file ``conf.py``::

  PARALLEL_NUMER = 2

Use the command ``auto_engage`` as the way used before.

Crontab Job
-----------

#. Go to the project root directory, and create a directory named ``tasks``::

   $ cd ~/workspace/surviral_avd
   $ mkdir tasks

#. Create a file ``tasks/environment.sh`` to include all required environment variables
   (the path of java, android, node, appium, adb, etc.)(copy them from ``~/.bashrc`` or
   copy the output of the command ``env`` with preceding ``export`` for every line)::

    export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
    export MANPATH="/home/linuxbrew/.linuxbrew/share/man:$MANPATH"
    export INFOPATH="/home/linuxbrew/.linuxbrew/share/info:$INFOPATH"

    export PATH="$HOME/task_bin/:$PATH"
    export PATH="$HOME/.android/sdk/cmdline-tools/latest/bin:$HOME/.android/sdk/platform-tools:$HOME/.android/sdk/emulator:$HOME/.android/sdk/avd:$PATH"
    export ANDROID_SDK_ROOT="$HOME/.android/sdk"
    export ANDROID_HOME="$HOME/.android/sdk"
    export ANDROID_AVD_HOME="$HOME/.android/sdk/avd"
    export JAVA_HOME="/usr/lib/jvm/java-8-openjdk-amd64"
    export PATH=${PATH}:${JAVA_HOME}/bin

    # for GUI software
    export DISPLAY=:0

#. Find an environment variable ``DISPLAY`` and add it the the file ``environment.sh``::

    (env) ibm@ibm-HP-EliteDesk-800-G2-SFF:~/workspace/surviral_avd$ env|grep DISPLAY
    DISPLAY=:0

#. Find the path of ``python`` or activate the python virtual environment::

     ibm@ibm-HP-EliteDesk-800-G2-SFF:~/workspace/surviral_avd$ source env/bin/activate
     (env) ibm@ibm-HP-EliteDesk-800-G2-SFF:~/workspace/surviral_avd$ which python
     /home/ibm/workspace/surviral_avd/env/bin/python

   Or::

     . env/bin/activate

#. Create a task file e.g. ``tasks/auto_engage.sh``, and run the above file ``environment.sh`` within it,
   then create the automation task::

    # project path
    export CURRENT_DIR=`dirname $(readlink -f $0)`
    export PRJ_DIR=`dirname $CURRENT_DIR`

    # go to project root directory
    cd $PRJ_DIR

    # activate the virtual environment for python
    . env/bin/activate

    # import environment variables
    . ./tasks/environment.sh

    # run task
    python manage.py auto_engage
    #/home/ibm/workspace/surviral_avd/env/bin/python manage.py auto_engage

#. Create crontab job(``crontab -e``)::

   * * * * * /bin/bash /home/ibm/workspace/surviral_avd/tasks/auto_engage.sh 2>&1 > /home/ibm/workspace/surviral_avd/tasks/auto_engage.log

The method of creating automation task and crontab job automatically
(Run the script ``create_task.py``)::

  $ python create_task.py  --cmds auto_engage --args ' --no_vpn' --jobs '30 22 * * *'
  $ python create_task.py  --cmds auto_engage update_profile --args ' --no_vpn' ' --no_vpn' --jobs '30 22 * * *' '30 22 * * *'

Achieve specific engagement number
----------------------------------

#. Setup database::

    $ python manage.py setup --database

#. Setup the engagement numbers and target users in file ``accounts_conf.py``::

    # engagement number in a week
    LIKE_MIN_NUMBER_IN_A_WEEK = 150
    RETWEET_MIN_NUMBER_IN_A_WEEK = 100
    COMMENT_MIN_NUMBER_IN_A_WEEK = 30

    NEW_POST_EXTERNAL_USER_NAMES = [
        'xanalia_nft',
        'xana_metaverse',
        'xanametaverse',
        'rio_noborderz',
        'xanalia_promo_',
        'xanalia_promo',
        'ultramannft',
        'nftnewznet',
    ]

   Setup different target users on different PCs, or setup different engagement numbers for the same
   target users on different PCs.

   Pay attention to the total engagement number for the same target user on different PCs.

#. Run the command ``auto_manage``::

    $ python manage.py auto_manage

   First, the given engagement number will be divided to a quota
   for every day in a week, and the quota increases with the order of a day in a week.

   like quota(of a day in a week) = LIKE_MIN_NUMBER_IN_A_WEEK / 7 * <the order of the day in a week>(i.e. 1-7)

   This command will get the day in a week, then get it's quota, then check if
   the quota is greater than the corresponding number in DB for every actions
   on a specific tweet, if it doesn't achieve the quota,
   then run the command ``auto_engage`` once more, then check the number again,
   if it still doesn't achieve, wait for an interval(0.5h - 1h),
   next run ``auto_engage`` again until it achieves the quota of the day.

#. Print the statistics of engagement number in DB::

    $ python manage.py report_engage

Management Strategy
-------------------

Please think about how to run the bot according to the specific requirements(Management Strategy).

- Use different time in crontab job for all PCs
- Use differen target accounts in ``accounts_conf.py`` for all PCs, and setup the following values accordingly::

    # engagement number in a week
    LIKE_MIN_NUMBER_IN_A_WEEK = 150
    RETWEET_MIN_NUMBER_IN_A_WEEK = 100
    COMMENT_MIN_NUMBER_IN_A_WEEK = 30

- Update other accounts in ``accounts_conf.py`` frequently on one PC
- Update target accounts in ``accounts_conf.py`` frequently on one PC
- Update ``TWEET_KEYWORDS`` in ``accounts_conf.py`` occasionally on one PC
- Setup proper value of ``--latest_post_number`` for command ``auto_engage``
  according to the frequency of creating tweet for target accounts.
- Use these options like ``--target_like_chance`` for actions of target accounts,
  don't use the combination of options ``--must_follow --must_like --must_comment --must_retweet``::

    $ python manage.py auto_engage --for_new_post_only --no_vpn --target_follow_chance 3 --target_like_chance 2 --target_comment_chance 5 --target_retweet_chance 3 --no_skip_accounts

- Make sure the right steps to update code, or the bot cannot run correctly

  1. git pull
  2. python manage.py setup -d  (make sure all migration are created and implemented in DB)
  3. run the command you want


Usage
=====

Credentials of anydesk
----------------------

Address: 605242296
Password: #Instabot@123

ibm10/1234

Create accounts
---------------

::

   ./manage.py create_accounts -n=1


Database Operations
-------------------

Find the accounts of twitter::

  $ sudo -u postgres psql

  postgres=# \c surviral_avd

  surviral_avd=# \a

  surviral_avd=# \d

  surviral_avd=# select * from twbot_twitteraccount;

Copy outputs of query to a file::

  surviral_avd=# \copy (select * from twbot_twitteraccount) to 'account.csv' csv header;

Command Usage
-------------

::

  $ python manage.py update_profile --no_vpn --names android_387

  $ python manage.py create_accounts -n=1 -m=1 --no_vpn

  $ python manage.py write_tweet --no_vpn --names android_213 -f image -t ~/Downloads/program.jpg

  $ python manage.py write_tweet --no_vpn --names android_450 -f text -t "hello, this is the first tweet"

  $ python manage.py engage_with_link --no_vpn --names android_450 --job_id 1

  $ python manage.py engage --name android_450 --no_vpn --target enews --likes 1 --follows 1 --comments 1 --retweets 1

  $ python manage.py auto_engage --names android_450 --no_vpn

  $ python manage.py engage_with_link --no_vpn --job_id 1 --names android_269

  $ # use tweet API to get tweet for one device
  $ python manage.py write_tweet --no_vpn -f text --names android_269

  $ # use tweet API to get tweet for multiple random devices
  $ python manage.py write_tweet --no_vpn -f text

  $ # use tweet API to get tweet for all devices
  $ python manage.py write_tweet --no_vpn -f text --all_avds

  $ # run command auto_engage and write tweet for all accounts
  $ python manage.py auto_engage --no_vpn; python manage.py write_tweet --no_vpn -f text --all_avds


Optimization
============

Strategy
--------

General Strategy
~~~~~~~~~~~~~~~~

  Emulate all factors(at leat the key factors) in real environment as much as possible.

Factors in real environment

  - Human
  - Device(Phone and APP)
  - Network

Factors about Human
~~~~~~~~~~~~~~~~~~~

  - Operation and it's metadata

    - click
    - slide
    - view(check other person's content)
    - write
    - almost always online(don't loggin the account regularly)
    - login the account almost on the same device
    - interval between two operations

  - Content(result generated by operation) and it's metadata

    - profile
    - tweet's content
    - comment
    - retweet
    - like
    - share
    - follower
    - following
    - form of content(text, image, video, and so on)
    - type of content(life, advertisement, fact, thinking, etc.)

Factors about Device
~~~~~~~~~~~~~~~~~~~~

  - name
  - language
  - region
  - Model
  - serial number
  - IMEI
  - android version
  - build number
  - baseband version
  - Apps installed

Factors about Network
~~~~~~~~~~~~~~~~~~~~~

  - IP(whether it is from proxy server)
  - Region
  - URL


Practical Strategy
------------------

Write more comments, logs, docs, and tests.

Key factors about human
~~~~~~~~~~~~~~~~~~~~~~~

- Random password

  Now, the password of an account has some special characteristics:

  Some passwords begin with the string 'Ang1' and has the same length.

  For example::

    screen_name	        phone	        password
    JairusSchreiner	19125217389	Ang1yE1l
    ReevaHeine	        17194138289	Ang1KALi
    WesolowskiBrodi	15023247632	Ang1Kqew
    cecil_lafferty	17865716683	Ang1s7Lp
    AmoretteCutting	18504006418	Ang1UmkO
    AzureEldredge	12516470257	Ang1gawV
    SaucedaTeddy	15634246274	Ang1pFiq
    halley_wight	12602380612	Ang1mpID
    CamdenSkilar	15854967344	Ang1oRgi
    AlizaPeralta	17063837397	Ang1LBj8
    EversRio	        17014841209	Ang1Pei9
    AnnalyLambrecht	13057414182	Ang1R8dR

- Phone number matching with country

  - Create all accounts with the same country (USA)

- Setup profile

  - Add a picture to the account

    Almost all accounts have no picture.

- Provide other random operations
- Create some contents sometimes
- login the account or operating on the same device
- don't logout or offline immediately after some operations
- pay attention to the interval between two operations
- random content(follower, following, etc) and update them frequently

Key factors about Device
~~~~~~~~~~~~~~~~~~~~~~~~

- Bind device and the user's account

  Save the device which created the user's account, then loggin or operate on the same device. 

  At least, we can create the same device if necessary.

- Create the emulator which is like real phone as much as possible

Key factors about Network
~~~~~~~~~~~~~~~~~~~~~~~~~

At present, I think we don't need think about these factors.

Script Optimization
-------------------

Content
~~~~~~~

Please add more and update contents in the file ``constants.py`` and ``accounts_conf.py``

command auto_engage 
~~~~~~~~~~~~~~~~~~~

- ``def follow_internal_accounts(avds):``

  - don't follow all internal accounts one time
  - add other followings except the internal accounts
  - add the following number and other accounts to the file ``accounts_conf.py``,
    please update them regularly

- ``def do_actions_for_new_post(self, avds):``

  - ``user_names = ["rhian_highsmith"]``, just one username, please add more usernames
  - add more usernames to the file ``accounts_conf.py``

- Openning other account's profile using webview is failed sometimes, we should find another way
  to open the profile::

    load_url_btn = self.driver(
            ).find_elements_by_accessibility_id('Load URL')
    load_url_btn1 = self.driver().find_elements_by_xpath(
            '//android.widget.ImageButton[@content-desc="Load URL"]')
    load_url_btn = load_url_btn or load_url_btn1
    if load_url_btn:
        LOGGER.debug('click button "Go" of webview')
        load_url_btn[0].click()
        random_sleep(5, 10)
    self.driver().press_keycode(66)

- ``def do_actions_for_new_post(self, avds, no_comment=False):``

  - Added options(like 3 latest posts of accounts only in the NEW_POST_EXTERNAL_USER_NAMES)::

      --must_like            # only for users in NEW_POST_EXTERNAL_USER_NAMES
      --must_follow          # only for users in NEW_POST_EXTERNAL_USER_NAMES
      --must_retweet         # only for users in NEW_POST_EXTERNAL_USER_NAMES
      --for_new_post_only    # for test, don't use it for product environment
      --latest_post_number 3 # how many of latest posts do the actions perform on, only for users in NEW_POST_EXTERNAL_USER_NAMES

      python manage.py auto_engage --no_vpn --must_like --must_follow --must_retweet --for_new_post_only --no_comment --latest_post_number 3 --names android_199

  - Add one variable in ``accounts_conf.py`` (It should perform action on atleast 2 usernames
    from NEW_POST_EXTERNAL_USER_NAMES variable)::

      NEW_POST_EXTERNAL_USER_NAMES_NUMBER = 2  # the number to select randomly

Account
~~~~~~~

- Some pictures from unsplash.com are not suitable for profile picture,
  e.g. a picture with blood

- One picture for one account from unsplash.com maybe the same one for other account
- Phone number provided by API may be used ago, and twitter will give a tips about it.

  tip: This phone number is already registered to an account.

Version
~~~~~~~

- Download more apks of twitter, and put them into 'apk/twitter_<version>.apk',
  and update the variable ``TWITTER_VERSIONS`` in the file ``accounts_conf.py``.

  The script will select a random version to install.

  Download it from https://www.apkmonk.com/app/com.twitter.android/

- Android version

  Configure and download more packages of android(architecture just be ``x86`` or ``x86_64``),
  and put the package name into the list of ``AVD_PACKAGES`` in the file ``accounts_conf.py``.

  This version '9.11.0-release.00' and the following versions require google play services.


Device
~~~~~~

- Kill process gracefully in order to let the emulator rememeber the last state, that is
  keeping the account logged in.(``twbot/bot.py``)


Captcha
~~~~~~~

- new Captcha form, and the bot cannot resolve it correctly.

  The new reCAPTCHA form appears all version of twitter.

  .. image:: ./recaptcha1.png

  .. image:: ./recaptcha2.png

- Cannot bypass FunCaptcha using Coordinates API of deathbycaptcha.

  Because the rate of recognizing FunCaptcha images is low.

- Cannot use Funcaptcha API of deathbycaptcha on android.

  Because this API requires publickey and pageurl which cannot be found
  on android.

- FunCaptcha is found on all versions of twitter(including 8.84), I think all types of captcha
  can be found on all versions of twitter.

- If the captcha is hard to bypass, and after several days,
  twitter will decrease the complexity of it. 

  Then it is relatively easy to bypass captcha.

  Don't repeat too many times of bypassing captcha at one time if it fails many times.

- The methods bypassing Captcha (for Android APP)

  - Using Human-powered CAPTCHA-solving service

    For example, https://2captcha.com/

    Two universal methods for image based captcha:

    - Grid

      https://2captcha.com/2captcha-api#grid

      This method allows to solve any captcha where image can be divided
      into equal parts like reCAPTCHA V2 or hCaptcha. A grid is applied above the image.
      And you receive the numbers clicked boxes.

    - Coordinates

      https://2captcha.com/2captcha-api#coordinates

      This method allows you to solve any captcha that requires clicking on images,
      like reCAPTCHA V2, hCaptcha, etc.

  - Using `Death By Captcha API`__

    __ https://deathbycaptcha.com/

    Please refer to `CAPTCHA Configure for Android`_


Network Traffic
===============

Those are intercepted through web browser.

Conclusions
-----------

Twitter collects almost all information from device, user's operations, user's inputs, network,
and other apsects.

Issues
------

- Cannot analyze twitter's network traffic because of its built-in certificate(SSL Pinning)
- Cannot analyze twitter's network traffic in browser's phone emulator(using Chromium)

  It will display the blank page after entering username, password and phone number.

  But can analyze its network traffic using Firefox.

Request Headers
---------------

- user agent

  ::

    user-agent: Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Mobile Safari/537.36

    User-Agent: Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36

- accept-language

  ::

    accept-language: en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7

- Referer

  ::

    Referer: https://mobile.twitter.com/

- Cookie

  ::

    Cookie: personalization_id="v1_QGLYG3SRKABqm8xyjI3VvA=="; guest_id=v1%3A163644976374906358; ct0=4edcbb83512369ea6d29722c1fc69cca; gt=1458002120796368901

Request Data
------------

- username, password, and phone number

  ::

    {"flow_token":"g;163644760333667609:-1636447603345:Hz4nem7CItM8iD6eDNDFoB47:6","subtask_inputs":[{"subtask_id":"LoginEnterPassword","enter_password":{"password":"Ang1oRgi","link":"next_link"}}]}

    {"flow_token":"g;163644760333667609:-1636447603345:Hz4nem7CItM8iD6eDNDFoB47:7","subtask_inputs":[{"subtask_id":"LoginAcid","enter_text":{"text":"15854967344","link":"next_link"}}]}

- time(duration)

  ::

    category: perftown
    log: [{"description":"rweb:heartbeat:health:true","product":"rweb","duration_ms":540000,"metadata":"529c4604-6f95-4a24-b5d5-4ebf695672e2","device_info":{"available_heap":4294705152},"mem_metrics":{"native_total_max":26458875,"native_total_avg":24922011}}]

- client type

  ::

    "event_namespace":{"page":"onboarding","element":"link","action":"click","client":"m5"}

- device info

  (There are some notifications about loggin devices in the tab 'notifications' of twitter)

  ::

    [{"description":"rweb:heartbeat:health:true","product":"rweb","duration_ms":780000,"metadata":"529c4604-6f95-4a24-b5d5-4ebf695672e2","device_info":{"available_heap":4294705152},"mem_metrics":{"native_total_max":26945597,"native_total_avg":25437457}}]

    {"index":"responsive_web_prod","type":"ERROR","id":1636449805222,"source":{"browserSupport":"3","runtime":"browser","userAgent":"Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36","url":"https://mobile.twitter.com/home","@timestamp":"2021-11-09T09:23:25.222Z","message":"DiskStorageUnavailableError: Disk Storage is unavailable for this client","extra":"{\"unhandledPromiseRejection\":true}","sha":"fdc5e940a41689d69e32c350f82cf7eae6e835ca","error_details":"c@https://abs.twimg.com/responsive-web/client-web/main.2a3eb6b5.js:1:195527\n_withStore@https://abs.twimg.com/responsive-web/client-web/main.2a3eb6b5.js:1:197269\niterate@https://abs.twimg.com/responsive-web/client-web/main.2a3eb6b5.js:1:198955\nsetUserId@https://abs.twimg.com/responsive-web/client-web/main.2a3eb6b5.js:1:558252\nhe/</<@https://abs.twimg.com/responsive-web/client-web/main.2a3eb6b5.js:1:717051\nc@https://abs.twimg.com/responsive-web/client-web/main.2a3eb6b5.js:9:97220\nm/</<@https://abs.twimg.com/responsive-web/client-web/main.2a3eb6b5.js:9:97288\n"},"tag":"UnknownCustomError"}

- operation and event(start timestamp, sequence number)

  Twitter will record all operations and events when the user is operating.

  api: https://api.twitter.com/1.1/jot/client_event.json

  ::

    [{"_category_":"client_event","format_version":2,"triggered_on":1636462978423,"items":[{"item_type":0,"id":"1458053752280158210","sort_index":"7765343697787076505","suggestion_details":{"controller_data":"DAACDAAEDAABCgABYAQKIIAOGAUAAAAA"},"conversation_details":{"conversation_section":"HighQuality"},"impression_details":{"visibility_start":1636462970403,"visibility_end":1636462978421},"author_id":"1441276797107073030","in_reply_to_tweet_id":"1458028339067699202","in_reply_to_author_id":"3437532637","is_viewer_follows_tweet_author":false,"is_tweet_author_follows_viewer":false,"is_viewer_super_following_tweet_author":false,"is_viewer_super_followed_by_tweet_author":false,"is_tweet_author_super_followable":false,"engagement_metrics":{"reply_count":0,"retweet_count":0,"favorite_count":0,"quote_count":0}},{"item_type":0,"id":"1458035069268873219","sort_index":"7765343697787076485","suggestion_details":{"controller_data":"DAACDAAEDAABCgABYAQGIIAcCAUAAAAA"},"conversation_details":{"conversation_section":"HighQuality"},"impression_details":{"visibility_start":1636462970516,"visibility_end":1636462978421},"author_id":"1442516028060155911","in_reply_to_tweet_id":"1458028339067699202","in_reply_to_author_id":"3437532637","is_viewer_follows_tweet_author":false,"is_tweet_author_follows_viewer":false,"is_viewer_super_following_tweet_author":false,"is_viewer_super_followed_by_tweet_author":false,"is_tweet_author_super_followable":false,"engagement_metrics":{"reply_count":0,"retweet_count":0,"favorite_count":0,"quote_count":0}},{"item_type":0,"id":"1458029224602734601","sort_index":"7765343697787076475","suggestion_details":{"controller_data":"DAACDAAEDAABCgABYAQGIIgMCAUAAAAA"},"conversation_details":{"conversation_section":"HighQuality"},"impression_details":{"visibility_start":1636462971005,"visibility_end":1636462978421},"author_id":"1457719014134726658","in_reply_to_tweet_id":"1458028339067699202","in_reply_to_author_id":"3437532637","is_viewer_follows_tweet_author":false,"is_tweet_author_follows_viewer":false,"is_viewer_super_following_tweet_author":false,"is_viewer_super_followed_by_tweet_author":false,"is_tweet_author_super_followable":false,"engagement_metrics":{"reply_count":0,"retweet_count":0,"favorite_count":0,"quote_count":0}},{"item_type":0,"id":"1458039598244786178","sort_index":"7765343697787076465","suggestion_details":{"controller_data":"DAACDAAEDAABCgABYAQGIJAMCAUAAAAA"},"conversation_details":{"conversation_section":"HighQuality"},"impression_details":{"visibility_start":1636462973540,"visibility_end":1636462978421},"author_id":"1297055907235237889","in_reply_to_tweet_id":"1458028339067699202","in_reply_to_author_id":"3437532637","is_viewer_follows_tweet_author":false,"is_tweet_author_follows_viewer":false,"is_viewer_super_following_tweet_author":false,"is_viewer_super_followed_by_tweet_author":false,"is_tweet_author_super_followable":false,"engagement_metrics":{"reply_count":0,"retweet_count":0,"favorite_count":0,"quote_count":0}},{"item_type":0,"id":"1458028851913584643","sort_index":"7765343697787076455","suggestion_details":{"controller_data":"DAACDAAEDAABCgABYAQGIKAMCAUAAAAA"},"conversation_details":{"conversation_section":"HighQuality"},"impression_details":{"visibility_start":1636462973653,"visibility_end":1636462978421},"author_id":"713938254643343360","in_reply_to_tweet_id":"1458028339067699202","in_reply_to_author_id":"3437532637","is_viewer_follows_tweet_author":false,"is_tweet_author_follows_viewer":false,"is_viewer_super_following_tweet_author":false,"is_viewer_super_followed_by_tweet_author":false,"is_tweet_author_super_followable":false,"engagement_metrics":{"reply_count":0,"retweet_count":0,"favorite_count":0,"quote_count":0}}],"event_namespace":{"page":"tweet","component":"stream","element":"linger","action":"results","client":"m5"},"client_event_sequence_start_timestamp":1636449769086,"client_event_sequence_number":153,"client_app_id":"3033300"}]

    [{"_category_":"client_event","format_version":2,"triggered_on":1636463491169,"items":[],"event_namespace":{"page":"messages","section":"inbox","component":"inbox_timeline","action":"show","client":"m5"},"client_event_sequence_start_timestamp":1636449769086,"client_event_sequence_number":206,"client_app_id":"3033300"}]

    [{"_category_":"client_event","format_version":2,"triggered_on":1636464094936,"items":[],"event_namespace":{"page":"compose","section":"composition","element":"send_tweet","action":"click","client":"m5"},"client_event_sequence_start_timestamp":1636449769086,"client_event_sequence_number":238,"client_app_id":"3033300"}]

- User's input and the metadata

  tweet's content, retweet, like, comment,

  The contents of all user's inupt should not be all advertisements,
  and should add other content apart from advertisements.

  ::

    {"tweet_text":"hello XANALIA!","media":{"media_entities":[],"possibly_sensitive":false},"withReactionsMetadata":false,"withReactionsPerspective":false,"withSuperFollowsTweetFields":true,"withSuperFollowsUserFields":true,"withNftAvatar":false,"semantic_annotation_ids":[],"dark_request":false,"withUserResults":true,"withBirdwatchPivots":false}


Tests
=====

Run tests::

  $ python -m unittest tests.test_get_username.TestUsername
  $ python -m unittest tests.test_get_username.TestUsername.test_get_random_username

  $ python -m unittest tests.test_get_password.TestPassword.test_get_real_random_password

Create accounts tests

Failed accounts::

  ********************
  Name: Grayson Reed
  Password: DYQSDvw'n,
  Phone: 12252449312
  Country: United States #9486
  ********************


Android
=======

`How to install Android SDK and setup AVD Emulator without Android Studio`__

__ https://medium.com/michael-wallace/how-to-install-android-sdk-and-setup-avd-emulator-without-android-studio-aeb55c014264

`Android Command line tools`__

__ https://developer.android.com/studio/command-line/

AVD Setup
---------

Export environment variables::

  export PATH="$HOME/.android/sdk/cmdline-tools/latest/bin:$HOME/.android/sdk/platform-tools:$HOME/.android/sdk/emulator:$HOME/.android/sdk/avd:$PATH"
  export ANDROID_SDK_ROOT="$HOME/.android/sdk"
  export ANDROID_HOME="$HOME/.android/sdk"
  export ANDROID_AVD_HOME="$HOME/.android/sdk/avd"
  export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
  export PATH=${PATH}:${JAVA_HOME}/bin

List all packages installed (the first items on the list) and all packages available to download::

  ./sdkmanager --list --sdk_root=/home/test/.android/sdk

Download the packages, simply copy the package names and pass it as a parameter
to the SDKManager CLI using the terminal::

  ./sdkmanager --list --sdk_root=/home/test/.android/sdk platform-tools emulator

Create AVD and run it::

  avdmanager create avd --name android_99 --package "system-images;android-28;default;x86"
  emulator -avd android_99

`List of tz database time zones`__

__ https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

Install system image::

  $ sdkmanager "system-images;android-30;default;arm64-v8a"

Create AVD::

  $ avdmanager create avd -n test1 -k "system-images;android-30;default;arm64-v8a"

  $ emulator -list-avds

Emulator options::

  $ emulator -avd android_197 -no-snapshot -camera-back emulated -camera-front emulated -timezone  US/Eastern -no-boot-anim -shell

Network Traffic
---------------

Request URL::

  https://104.244.42.66/1.1/strato/column/None/1460834681784442880,a05948e1-cb55-4bee-972b-4ac30b00ee60,geoLocation/clients/permissionsState

Request header::

  timezone:                   Asia/Shanghai
  os-security-patch-level:    2018-08-05
  optimize-body:              true
  accept:                     application/json
  x-twitter-client:           TwitterAndroid
  user-agent:                 TwitterAndroid/8.84.0-release.00 (28840000-r-0) Android+SDK+built+for+x86/9
                              (unknown;Android+SDK+built+for+x86;Android;sdk_phone_x86;0;;1;2013)
  accept-encoding:            zstd, gzip, deflate
  x-twitter-client-language:  en-US
  x-client-uuid:              a05948e1-cb55-4bee-972b-4ac30b00ee60
  x-twitter-client-deviceid:  ae031ccc9c2141ae
  authorization:              OAuth realm="http://api.twitter.com/", oauth_version="1.0",
                              oauth_token="1460834681784442880-KQxzAqDhKd7ynd0yY1v46PY1snjQO2",
                              oauth_nonce="29305063805831926415224774538319", oauth_timestamp="1637419174",
                              oauth_signature="WrsRmfVd7XuLPmsBGcwUp8TQiQs%3D", oauth_consumer_key="3nVuSoBZnx6U4vzUxf5w",
                              oauth_signature_method="HMAC-SHA1"
  x-twitter-client-version:   8.84.0-release.00
  cache-control:              no-store
  x-twitter-active-user:      yes
  x-twitter-api-version:      5
  x-b3-traceid:               256c14a43e1960f8
  kdt:                        qiiHz0BGGEskRmZfJZlGxQa9DoZYHyfVxDBhPHx3
  accept-language:            en-US
  x-twitter-client-flavor:
  content-type:               application/json
  content-length:             343
  cookie:                     personalization_id=v1_8SvwtFqQi8AlOsRxSd54dA==; guest_id_marketing=v1%3A163741818320017621;
                              guest_id_ads=v1%3A163741818320017621; guest_id=v1%3A163741818320017621

Request content::

  {
      "androidChannelSettings": {},
      "clientApplicationId": "258901",
      "clientVersion": "8.84.0-release.00",
      "deviceId": "a05948e1-cb55-4bee-972b-4ac30b00ee60",
      "inAppPermissionState": {
          "Off": null
      },
      "metadata": {},
      "osVersion": "9",
      "permissionName": "geoLocation",
      "systemPermissionState": {
          "Off": null
      },
      "timestampInMs": "1637419173960",
      "userId": "1460834681784442880"
  }


Request 1 URL::

  POST https://104.244.42.66/1.1/jot/client_event

Request 1 header::

  timezone:                   Asia/Shanghai
  os-security-patch-level:    2018-08-05
  optimize-body:              true
  accept:                     application/json
  x-twitter-client:           TwitterAndroid
  user-agent:                 TwitterAndroid/8.84.0-release.00 (28840000-r-0) Android+SDK+built+for+x86/9
                              (unknown;Android+SDK+built+for+x86;Android;sdk_phone_x86;0;;1;2013)
  accept-encoding:            zstd, gzip, deflate
  x-twitter-client-language:  en-US
  x-client-uuid:              a05948e1-cb55-4bee-972b-4ac30b00ee60
  x-twitter-client-deviceid:  ae031ccc9c2141ae
  authorization:              OAuth realm="http://api.twitter.com/", oauth_version="1.0",
                              oauth_token="1460834681784442880-KQxzAqDhKd7ynd0yY1v46PY1snjQO2",
                              oauth_nonce="31040123188637106089489108894090", oauth_timestamp="1637419350",
                              oauth_signature="asTDzwi6lB4ud6DC3wAjaiP4XwM%3D", oauth_consumer_key="3nVuSoBZnx6U4vzUxf5w",
                              oauth_signature_method="HMAC-SHA1"
  x-twitter-client-version:   8.84.0-release.00
  cache-control:              no-store
  x-twitter-active-user:      no
  x-twitter-api-version:      5
  x-b3-traceid:               424a4e1164475ba8
  kdt:                        qiiHz0BGGEskRmZfJZlGxQa9DoZYHyfVxDBhPHx3
  accept-language:            en-US
  x-twitter-client-flavor:
  content-encoding:           gzip
  content-type:               application/x-www-form-urlencoded
  content-length:             458
  cookie:                     personalization_id=v1_8SvwtFqQi8AlOsRxSd54dA==; guest_id_marketing=v1%3A163741818320017621;
                              guest_id_ads=v1%3A163741818320017621; guest_id=v1%3A163741818320017621; lang=en

Request 1 content::

  log:  [{"_category_":"client_event","format_version":2,"event_name":"android:home:home:stream::results","ts":1637419291800,"stream_id
  ":0,"content_length":0,"event_initiator":2,"items":[{"position":1,"suggestion_details":{"suggestion_type":"Message"}}],"client_event_
  sequence_start_timestamp":1637418758950,"client_event_sequence_number":30},{"_category_":"client_event","format_version":2,"event_nam
  e":"android:home:home:::results","ts":1637419291802,"stream_id":0,"content_length":0,"event_initiator":2,"items":[{"suggestion_detail
  s":{"suggestion_type":"Message"}}],"client_event_sequence_start_timestamp":1637418758950,"client_event_sequence_number":31},{"_catego
  ry_":"client_event","format_version":2,"event_name":"android:home:home:stream:linger:results","ts":1637419291812,"stream_id":0,"conte
  nt_length":0,"event_initiator":2,"items":[{"cursor":0,"visibility_start":1637419173874,"visibility_end":1637419291800,"suggestion_det
  ails":{"suggestion_type":"Message"}}],"client_event_sequence_start_timestamp":1637418758950,"client_event_sequence_number":32},{"_cat
  egory_":"client_event","format_version":2,"event_name":"android:app::::become_inactive","ts":1637419291823,"stream_id":0,"content_len
  gth":0,"duration_ms":600530,"items":[{"name":"addressBookPermissionStatus","description":"0"},{"name":"geoPermissionStatus","descript
  ion":"4"},{"name":"notificationPermissionSettings","description":"0"},{"name":"androidMPermissionsActive","description":"1"}],"client
  _event_sequence_start_timestamp":1637418758950,"client_event_sequence_number":33}]
  lang: en

Login Request URL::

  POST https://104.244.42.2/auth/1/xauth_password.json HTTP/2.0

Login Request header::

  timezone:                   America/Los_Angeles
  os-security-patch-level:    2018-08-05
  optimize-body:              true
  accept:                     application/json
  x-twitter-client:           TwitterAndroid
  user-agent:                 TwitterAndroid/8.84.0-release.00 (28840000-r-0) Android+SDK+built+for+x86/9
                              (unknown;Android+SDK+built+for+x86;Android;sdk_phone_x86;0;;1;2013)
  accept-encoding:            zstd, gzip, deflate
  x-twitter-client-language:  en-US
  x-client-uuid:              a05948e1-cb55-4bee-972b-4ac30b00ee60
  x-twitter-client-deviceid:  ae031ccc9c2141ae
  authorization:              Bearer AAAAAAAAAAAAAAAAAAAAAFXzAwAAAAAAMHCxpeSDG1gLNLghVe8d74hl6k4%3DRUMF4xAQLsbeBhTSRrCiQpJtxoGWeyHrDb
                              5te2jpGskWDFW82F
  x-twitter-client-version:   8.84.0-release.00
  cache-control:              no-store
  x-guest-token:              1462063944965623809
  x-twitter-active-user:      yes
  x-twitter-api-version:      5
  x-b3-traceid:               c7213e5ea859920c
  kdt:                        qiiHz0BGGEskRmZfJZlGxQa9DoZYHyfVxDBhPHx3
  accept-language:            en-US
  x-twitter-client-flavor:
  content-encoding:           gzip
  content-type:               application/x-www-form-urlencoded
  content-length:             652
  cookie:                     guest_id_marketing=v1%3A163742101058415245; guest_id_ads=v1%3A163742101058415245;
                              guest_id=v1%3A163742101058415245; personalization_id=v1_1njycI2AyPQ1+76X4Ghr5g==

Login Request content::

  x_auth_identifier:         Charlie98673776
  x_auth_password:           zJ9LNJIh|ix0G05}b
  send_error_codes:          true
  x_auth_login_challenge:    1
  x_auth_login_verification: 1
  ui_metrics:                {"rf":{"a40f9c74c3f096d0e79a998ca8789ff9744872bcd4afd9e803840b13c628c7ff":249,"d7f4f96357c4849ff11d869e6fe
  1e8769c375f83a4dfdf4e85ceec15c3fbe00b":156,"afb7cb55e6338e6e09a98ff471346dccc968e6dfd084a90466d279979ee0d6dc":185,"d1741aadcb47f9bb37
  a2a5df57dea77346842899a4653b73f02f2ce3a8c4f5a2":-1},"s":"65MyO67Fruev_LPtj3if4iXFAtOhhMlwR4-AOgtHCw2VFUDLXtWWKinlyic1sVcm6pyW3O7YzBdw
  sm7Abo-iGHKGv47PF1gpLKr6doCFAJ8r7zce04L4jMI_IrE2f_WPYU3iYAxU5GezfGecu7XR0pSVRm3fJgji2q4D3VCH82BIUPbuLrsBh7ux1ZFaO-CZ2Glnuni0Ceam5CH-S
  GGtq8LtFM_4cvq7JZlVQmAgJvIT25Fcql6hx9qZlqd2At2k4xgSFWQw8dyIn6wtNBZTI5i_ESW_2WBRSJTWtsrC41ottPyJZKigzYvCaFReO34pRDTnmjuSvmFhTYqmz7emlQ
  AAAX0953Tn"}

system-user-agent request URL::

  POST https://104.244.42.2/1.1/onboarding/task.json?flow_name=welcome&api_version=1&known_device_token=qiiHz0BGGEskRmZfJZlGxQa9DoZYHyfVxDBhPHx3 HTTP/2.0

system-user-agent request header::

  timezone:                   America/Los_Angeles
  os-security-patch-level:    2018-08-05
  optimize-body:              true
  accept:                     application/json
  x-twitter-client:           TwitterAndroid
  user-agent:                 TwitterAndroid/8.84.0-release.00 (28840000-r-0) Android+SDK+built+for+x86/9
                              (unknown;Android+SDK+built+for+x86;Android;sdk_phone_x86;0;;1;2013)
  system-user-agent:          Dalvik/2.1.0 (Linux; U; Android 9; Android SDK built for x86 Build/PSR1.180720.012)
  accept-encoding:            zstd, gzip, deflate
  x-twitter-client-language:  en-US
  x-client-uuid:              a05948e1-cb55-4bee-972b-4ac30b00ee60
  x-twitter-client-deviceid:  ae031ccc9c2141ae
  authorization:              Bearer AAAAAAAAAAAAAAAAAAAAAFXzAwAAAAAAMHCxpeSDG1gLNLghVe8d74hl6k4%3DRUMF4xAQLsbeBhTSRrCiQpJtxoGWeyHrDb
                              5te2jpGskWDFW82F
  x-twitter-client-version:   8.84.0-release.00
  twitter-display-size:       1080x2208x440
  os-version:                 28
  cache-control:              no-store
  x-guest-token:              1462063944965623809
  x-twitter-active-user:      yes
  x-twitter-api-version:      5
  x-b3-traceid:               fca36987b5bf4864
  kdt:                        qiiHz0BGGEskRmZfJZlGxQa9DoZYHyfVxDBhPHx3
  accept-language:            en-US
  x-twitter-client-flavor:
  content-encoding:           gzip
  content-type:               application/json
  content-length:             384
  cookie:                     guest_id_marketing=v1%3A163742101058415245; guest_id_ads=v1%3A163742101058415245;
                              guest_id=v1%3A163742101058415245; personalization_id=v1_1njycI2AyPQ1+76X4Ghr5g==

system-user-agent request content::

  {
      "flow_token": null,
      "subtask_versions": {
          "alert_dialog": 1,
          "alert_dialog_suppress_client_events": 1,
          "check_logged_in_account": 0,
          "choice_selection": 2,
          "contacts_live_sync_permission_prompt": 2,
          "cta": 5,
          "cta_inline": 1,
          "email_verification": 2,
          "end_flow": 1,
          "enter_email": 1,
          "enter_password": 5,
          "enter_phone": 1,
          "enter_text": 4,
          "enter_username": 2,
          "fetch_temporary_password": 1,
          "generic_urt": 1,
          "interest_picker": 3,
          "location_permission_prompt": 1,
          "menu_dialog": 1,
          "open_account": 1,
          "open_home_timeline": 1,
          "open_link": 1,
          "phone_verification": 1,
          "privacy_options": 1,
          "select_avatar": 1,
          "select_banner": 1,
          "settings_list": 3,
          "sign_up": 2,
          "sign_up_review": 1,
          "topics_selector": 1,
          "update_users": 1,
          "user_recommendations_list": 4,
          "user_recommendations_urt": 1,
          "wait_spinner": 1
      }
  }


