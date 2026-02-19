#####################################################################
############################ SETUP #################################

#clone 
git clone https://github.com/anjini2512/pyviyatools.git

#install
cd pyviyatools

pip install -r requirements.txt

# tell pyviyatools to look in a new location
./setup.py --clilocation /opt/sas/deploy/viya

# Confirm that its working
./showsetup.py

#####################################################################
############################ TROUBLESHOOT #################################

#if you do -ls and setconfigurationproperties_AS.py is not green, it means it is not executable. Run:
chmod +x setconfigurationproperties_AS2.py



#####################################################################
############################ APPLY CHANGES #################################
python3 getconfigurationproperties.py -c sas.compute.server -o json \
| jq '
  (.items[] | select(.name=="configuration_options") | .contents) |=
  (
    .
    + (if (. | contains("cas.DQSETUPLOC=")) then "" else "\ncas.DQSETUPLOC='\''QKB NAME'\''\n" end)
    + (if (. | contains("cas.DQLOCALE="))   then "" else "cas.DQLOCALE='\''ENUSA'\''\n"   end)
  )
' \
| python3 ./setconfigurationproperties_AS2.py --dryrun
``


#apply the changes. note: add --dryrun if you do not want to see changes
python3 getconfigurationproperties.py -c sas.compute.server -o json \
| jq '
  (.items[] | select(.name=="configuration_options") | .contents) |=
  (
    .
    + (if (. | contains("cas.DQSETUPLOC=")) then "" else "\ncas.DQSETUPLOC='\''QKB NAME'\''\n" end)
    + (if (. | contains("cas.DQLOCALE="))   then "" else "cas.DQLOCALE='\''ENUSA'\''\n"   end)
  )
' \
| python3 ./setconfigurationproperties_AS2.py
``


#check that it worked
python3 getconfigurationproperties.py -c sas.compute.server -o json \
| jq -r '.items[] | select(.name=="configuration_options") | .contents'


python3 getconfigurationproperties.py -c sas.compute.server -o json |jq .items[0]


