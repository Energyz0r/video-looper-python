#!/bin/bash
# Error out if anything fails.
set -e

# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# In ored for your script to update every dependencie and write very file, the script must be run by the root user.
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
   echo "Must be run as root with sudo! Try: sudo ./install.sh"
   exit 1
fi

# ----------------------------------------------------- START -------------------------------------------------------------------
# Directory where the script will be installed
WORKING_DIR="/usr/looper/"
# ------------------------------------------------------ END --------------------------------------------------------------------


# ----------------------------------------------------- START -------------------------------------------------------------------
# Short version of Wget
wget=/usr/bin/wget
# ------------------------------------------------------ END --------------------------------------------------------------------

# ----------------------------------------------------- START -------------------------------------------------------------------
# Google URL ID for the script to be downloaded
GOOGLE_DRIVE_ID="1-FGnbe2d1Z_Gk4RZrqmsG2LEttxmuL7Z"
# ------------------------------------------------------ END --------------------------------------------------------------------

# ----------------------------------------------------- START -------------------------------------------------------------------
# Service Variable used to define our service name
# ---IMPORTANT--- : Always must end with .service no matter what( loop.service, player.service, etc);
SERVICE_VAR="video.service" 
# ------------------------------------------------------ END --------------------------------------------------------------------

# ----------------------------------------------------------
# ----------------------------------------------------------
# Function that check if a specific service is active or not
# ----------------------------------------------------------
# ----------------------------------------------------------

is_service_exists() {
    local x=$1
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Checking for the status of the current service, if it is found we return 0, if it isn't we return 1
# '2> /dev/null' is put there to supress any error that might come when we check for the status.
# 'grep -Fq "Active:"' is the search for our pattern which is 'Active:' with '-F' tells we are searching for a fixed pattern and '-q' is for executing it quietly
# 'local x=$1' is the service we are looking for, in our case will be 'video.service'
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
    if systemctl status "${x}" 2> /dev/null | grep -Fq "Active:"; then
            return 0
    else
            return 1
    fi
}

# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------
# Install all the dependencies and set the python version to newest stable version (3.7)
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------

dependencies() {

    echo "Installing dependencies..."
    echo "==========================================="
	# --------------------------------------------------------------------------------------------
	# Update the system and install python 3 along with pip3(needed to install the VLC plugin)
	# --------------------------------------------------------------------------------------------		
    apt update && apt -y install python3 python3-pip wget

	# --------------------------------------------------------------------------------------------
	# Check if our major version of python equals 2, if true, we install the stable version of 3.7
	# --------------------------------------------------------------------------------------------
    ver=$(python -c"import sys; print(sys.version_info.major)")
    if [ $ver -eq 2 ]; then
        echo "Using Python 2.7 ! Updating..."
        update-alternatives --install /usr/bin/python python /usr/bin/python3.7 2
		
	# --------------------------------------------------------------------------------------------
	# Check if our major version of python equals 3, if true, print a message to the terminal
	# --------------------------------------------------------------------------------------------	
    elif [ $ver -eq 3 ]; then
        OUTPUT=`python --version | perl -pe '($_)=/([0-9]+([.][0-9]+))/'`
        echo "Using Python $OUTPUT"
    else 
        echo "Unknown Python version: $ver"
    fi
	
	# --------------------------------------------------------------------------------------------
	# If everything went fine, we proceed with installing the VLC for python
	# --------------------------------------------------------------------------------------------	
    pip3 install python-vlc
}

# ------------------------------------------------
# ------------------------------------------------
# Finishing message when scrips has been installed
# ------------------------------------------------
# ------------------------------------------------
finish_message() {
    echo "
    _____ ___ _   _ ___ ____  _   _ _____ ____  
    |  ___|_ _| \ | |_ _/ ___|| | | | ____|  _ \ 
    | |_   | ||  \| || |\___ \| |_| |  _| | | | |
    |  _|  | || |\  || | ___) |  _  | |___| |_| |
    |_|   |___|_| \_|___|____/|_| |_|_____|____/ 
    "
}

# ---------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
# Download looper script from Google Drive
# ---IMPORTANT--- : Sometimes when the internet is slow Google might think that we are a bot and ask us some clearance,
# we bypass that with '--no-check-certificate' unless the connection is really poor and we can't do nothing about that.
# ---------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------

loop_video() {

# ----------------------------------------------------------------------------------------------------------------
# Check if the script already exists by veryfing if the directory is there and re-download it into the file looper.py
# ----------------------------------------------------------------------------------------------------------------
if [ -d $WORKING_DIR ]; then
    echo "Script exist rewriting..."
    cd $WORKING_DIR
    $wget --no-check-certificate "https://docs.google.com/uc?export=download&id=${GOOGLE_DRIVE_ID}" -O looper.py
	
# -------------------------------------------------------------------------------------------------------------------------------
# If the directory doesn't exists we asume that this is the first time doing this and download the script into the file looper.py
# -------------------------------------------------------------------------------------------------------------------------------
else
    echo "Downloading script..."
    mkdir $WORKING_DIR
    cd $WORKING_DIR
    $wget --no-check-certificate "https://docs.google.com/uc?export=download&id=${GOOGLE_DRIVE_ID}" -O looper.py
fi
echo "==========================================="

# ---------------------------------------------------------
# ---------------------------------------------------------
# After downloading the script we proceed with the service
# ---------------------------------------------------------
# ---------------------------------------------------------

echo "Configuring looper to run on start..."
# -------------------------------------------------------------------------------------------------------------------------------
# Define our working file
# -------------------------------------------------------------------------------------------------------------------------------
FILE=/lib/systemd/system/$SERVICE_VAR

# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
# IF the looper exist we proceed with reinstalling it (maybe some older version of it has been installed) better make sure.
# IF not we write the config into the service file
# ----IMPORTANT--- : Stoping the service before overwriting help us bypass some errors like (any service that is running prevent us from writing it unless is stoped)
# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------

if [ -f "$FILE" ]; then
    echo "Looper already exist, reinstalling..."
    systemctl stop $SERVICE_VAR
    rm "$FILE"
    loop_video
else 
    echo "First installation, installing..."
cat <<EOF > "$FILE"
[Service]
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
ExecStart=/usr/bin/python3 "$WORKING_DIR"/looper.py
Restart=on-failure
RestartSec=60s
KillSignal=SIGTERM
TimeoutStopSec=20s

[Install]
WantedBy=graphical.target
EOF
# -------------------------------------------------------------------------------------------------------------------------------
# Enable the service after the writing is done
# *Environment=DISPLAY : our current display, counting starts from 0
# *Environment=XAUTHORITY : used to store cookies and files that the service create
# *ExecStart : our script execution line
# *Restart : in case of an error we restart the script
# *RestartSec : restart the script every 60 seconds until is up and running
# *KillSignal : kill the process via SIGTERM(a request to the program to terminate)
# *TimeoutStopSec : if the KillSignal is not working, after Xs the program will be terminated with the signal SIGKILL
# *WantedBy = graphical.target (runlevel 5, similar with default.target), need to start our process automatically on every boot
# -------------------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------------------------------------------
# Enable the service after the writing is done
# -------------------------------------------------------------------------------------------------------------------------------
    sudo systemctl enable $SERVICE_VAR
fi

# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
# IF /vid folder exists we delete everything from it and create another one with nothing in it.
# IF not we make the /vid folder 
# ---IMPORTANT--- : IF this check wasn't made we might get some old video files in our new script(and we do not want that)
# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------

if [ ! -d /home/pi/Desktop/vid ]; then
    mkdir /home/pi/Desktop/vid
fi

echo "==========================================="
}

# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
# Create the config looper where we gonna have our settings
# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
config_looper() {
# -------------------------------------------------------------------------------------------------------------------------------
# Define our working file
# -------------------------------------------------------------------------------------------------------------------------------
FILE=/home/pi/Desktop/config.ini

	# -------------------------------------------------------------------------------------------------------------------------
	# IF config already exists we delete it and rerun the function to create another one.
	# -------------------------------------------------------------------------------------------------------------------------
    if [ -f "$FILE" ]; then
        rm "$FILE"
        config_looper
    else 
	# -------------------------------------------------------------------------------------------------------------------------
	# IF not we create the config file with our settings in it and give writing and reading premissions (777).
	# -------------------------------------------------------------------------------------------------------------------------
    echo "Configuring looper config..."
cat <<EOF > "$FILE"
#VIDEO LOOPER CONFIGURATION FILE

[config]
#how many times is the loop active before switch, if the video duration is 01:00 min and we add 50 here, we do 1x50 and get 50 min of loop timer
loops = 5
#how many seconds is the 2nd video up for (duration in seconds)
sleep_between = 50
EOF
        chmod 777 "$FILE"
    fi

echo "==========================================="
}

# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
# Rewrite the command boot config file to make the VIDEO go into full screen without borders and detect the HDMI input
# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------

overwrite_config() {
    
cat <<EOF > "/boot/config.txt"
# For more options and information see
# http://rpf.io/configtxt
# Some settings may impact device functionality. See link above for details

# uncomment if you get no picture on HDMI for a default "safe" mode
#hdmi_safe=1

# uncomment this if your display has a black border of unused pixels visible
# and your display can output without overscan
disable_overscan=0
disable_splash=1
# uncomment the following to adjust overscan. Use positive numbers if console
# goes off screen, and negative if there is too much border
# The overscan changes based on TV screen resolution

overscan_left=5 
overscan_right=5
overscan_top=-10
overscan_bottom=-10

# uncomment to force a console size. By default it will be display's size minus
# overscan.
#framebuffer_width=1280
#framebuffer_height=720

# uncomment if hdmi display is not detected and composite is being output
hdmi_force_hotplug=1
display_auto_detect=1
# uncomment to force a specific HDMI mode (this will force VGA)
hdmi_group=1
hdmi_mode=1

# uncomment to force a HDMI mode rather than DVI. This can make audio work in
# DMT (computer monitor) modes
#hdmi_drive=2

# uncomment to increase signal to HDMI, if you have interference, blanking, or
# no display
config_hdmi_boost=4

# uncomment for composite PAL
#sdtv_mode=2

#uncomment to overclock the arm. 700 MHz is the default.
#arm_freq=800

# Uncomment some or all of these to enable the optional hardware interfaces
#dtparam=i2c_arm=on
#dtparam=i2s=on
#dtparam=spi=on

# Uncomment this to enable infrared communication.
#dtoverlay=gpio-ir,gpio_pin=17
#dtoverlay=gpio-ir-tx,gpio_pin=18

# Additional overlays and parameters are documented /boot/overlays/README

# Enable audio (loads snd_bcm2835)
dtparam=audio=on

[pi4]
# Enable DRM VC4 V3D driver on top of the dispmanx display stack
dtoverlay=vc4-fkms-v3d
max_framebuffers=2
boot_codedelay=10
[all]
#dtoverlay=vc4-fkms-v3d

EOF

echo "==================== Overwited config ======================"
}

# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
# Rewrite the command line for faster booting and full screen videos
# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------

overwrite_cmdline() {

cat <<EOF > "/boot/cmdline.txt"
console=serial0,115200 console=tty3 root=PARTUUID=ea7d04d6-02 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait silent quiet splash plymouth.ignore-serial-consoles plymouth.enable=0 loglevel=3 logo.nologo
EOF

echo "==================== Overwited cmdline ======================"
}

# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
# Delete all videos from the directory /vid
# -------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------
delete_video() {
	rm -rf /home/pi/Desktop/vid/*
	echo "==================== Empty /vid folder ======================"
}

install_script ()
{
	# -------------------------------------------------------------------------------------------------------------------------
	# We run the above functions in this order : 1. Install Dependencies
	#											 2. Overwrite Boot Config File
	#											 3. Overwrite Command Line
	#											 4. Install the script
	#											 5. Write the config file
	#											 6. Show finish message
	# -------------------------------------------------------------------------------------------------------------------------
    dependencies
    overwrite_config
    overwrite_cmdline	
    loop_video
    config_looper
    finish_message
    echo "---------Please reboot your machine---------"

}

reinstall_looper() {
	# -------------------------------------------------------------------------------------------------------------------------
	# We run the above functions in this order : 1. Install the script
	#											 2. Show finish message
	# -------------------------------------------------------------------------------------------------------------------------
    loop_video
    finish_message
}

reinstall_config() {
	# -------------------------------------------------------------------------------------------------------------------------
	# We run the above functions in this order : 1. Write the config file
	#											 2. Show finish message
	# -------------------------------------------------------------------------------------------------------------------------
    config_looper
    finish_message
}

uninstall_script() {
    echo "Uninstalling script and dependencies..."
	# -------------------------------------------------------------------------------------------------------------------------
	# Checking if the service exists
	# -------------------------------------------------------------------------------------------------------------------------
	
    if is_service_exists $SERVICE_VAR; then
        echo "Service found, proceed with uninstalling..."
		# -------------------------------------------------------------------------------------------------------------------------
		# 1.Stoping the service
		# 2.Disable the service
		# 3.Remove the service
		# 4.Reload services
		# 5.Remove the service if somehow got the Status: Failed
		# -------------------------------------------------------------------------------------------------------------------------		
        systemctl stop $SERVICE_VAR
        systemctl disable $SERVICE_VAR
        [ -f "/lib/systemd/system/$SERVICE_VAR" ] && rm /lib/systemd/system/$SERVICE_VAR
        systemctl daemon-reload
        systemctl reset-failed
    else
        echo "Service not found, nothing to remove"
    fi
	# -------------------------------------------------------------------------------------------------------------------------
	# 1.Removing /vid directory
	# 2.Removing config file
	# 3.Removing script file
	# -------------------------------------------------------------------------------------------------------------------------	
    [ -d /home/pi/Desktop/vid ] && rm -rf /home/pi/Desktop/vid
    [ -f "/home/pi/Desktop/config.ini" ] && rm /home/pi/Desktop/config.ini
    [ -f "/$WORKING_DIR/looper.py" ] && rm /$WORKING_DIR/looper.py
    echo "==========================================="
}


# -------------------------------------------------------------------------------------------------------------------------
# 												START KEYBOARD INPUT MENU SYSTEM
# -------------------------------------------------------------------------------------------------------------------------	

#define options as array
declare -a options

#set first empty position with new value
options[${#options[*]}]="Install Script";
options[${#options[*]}]="Reinstall Looper";
options[${#options[*]}]="Reinstall Looper Config";
options[${#options[*]}]="Delete Video";
options[${#options[*]}]="Uninstall Script";
options[${#options[*]}]="Quit";

#expand to quoted elements:
select opt in "${options[@]}"; do
  case ${opt} in
  ${options[0]}) install_script ;;
  ${options[1]}) reinstall_looper ;;
  ${options[2]}) config_looper ;;
  ${options[3]}) delete_video ;;
  ${options[4]}) uninstall_script ;;
  ${options[5]}) break; ;;
  (*) echo "${opt}"; ;;
  esac;
done

# -------------------------------------------------------------------------------------------------------------------------
# 												END KEYBOARD INPUT MENU SYSTEM
# -------------------------------------------------------------------------------------------------------------------------
