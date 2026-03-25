#####################################################################
############################ EDITING REPOSITORY PUSH/PULL #################################

###############################################
Push to GitHub from VS Code
Use PC's terminal

cd "C:\Users\ansamc\OneDrive - SAS\Documents\Python\pyviyatools"

git status 
-	To see your changes

git add .

git commit -m "Message”

git push

Enter passphrase: stars will shine

###############################################
How to update GitHub files in the VM PuTTy
Git pull



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



######################################################################################
############################ APPLY CHANGES - COMPUTE #################################
python3 getconfigurationproperties.py -c sas.compute.server -o json \
| jq '
  (.items[] | select(.name=="configuration_options") | .contents) |=
  (
    .
    + (if (. | contains("cas.DQSETUPLOC=")) then "" else "\ncas.DQSETUPLOC='\''QKB NAME'\''\n" end)
    + (if (. | contains("cas.DQLOCALE="))   then "" else "cas.DQLOCALE='\''ENUSA'\''\n"   end)
  )
' \
| python3 ./setconfigurationproperties_AS3.py --dryrun
``


#apply the changes
python3 getconfigurationproperties.py -c sas.compute.server -o json \
| jq '
  (.items[] | select(.name=="configuration_options") | .contents) |=
  (
    .
    + (if (. | contains("cas.DQSETUPLOC=")) then "" else "\ncas.DQSETUPLOC='\''QKB NAME'\''\n" end)
    + (if (. | contains("cas.DQLOCALE="))   then "" else "cas.DQLOCALE='\''ENUSA'\''\n"   end)
  )
' \
| python3 ./setconfigurationproperties_AS3.py
``


#check that it worked
python3 getconfigurationproperties.py -c sas.compute.server -o json \
| jq -r '.items[] | select(.name=="configuration_options") | .contents'


python3 getconfigurationproperties.py -c sas.compute.server -o json |jq .items[0]


######################################################################################
############################ APPLY CHANGES - CAS #################################

#to view the current sas.cas.instance.config config contents:
python3 getconfigurationproperties.py -c sas.cas.instance.config -o json \
| jq -r '.items[] | select(.name=="config")'

#dryrun test
python3 getconfigurationproperties.py -c sas.cas.instance.config -o json \
| jq '
  .version |= (. + 1)
  | (.items[] | select(.name=="config") | .contents) |=
    (
      .
      + (if (. | contains("cas.MYTESTOPTION=")) then "" else "\ncas.MYTESTOPTION='\''HELLO-AS-TEST'\''\n" end)
    )
' \
| python3 ./setconfigurationproperties_AS3.py -f - --dryrun

#Restart CAS
kubectl -n <your-namespace> rollout restart deploy cas-server-default


python3 getconfigurationproperties.py -c sas.cas.instance.config -o json |jq .items[0]