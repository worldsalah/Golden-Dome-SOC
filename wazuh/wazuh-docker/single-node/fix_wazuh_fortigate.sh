#!/bin/bash

CONTAINER="single-node-wazuh.manager-1"

echo "[1] Checking container..."
docker ps | grep $CONTAINER

if [ $? -ne 0 ]; then
    echo "Wazuh container not running"
    exit 1
fi


echo "[2] Backup current configuration..."
docker exec $CONTAINER bash -c \
"cp /var/ossec/etc/ossec.conf /var/ossec/etc/ossec.conf.backup"


echo "[3] Removing broken remote blocks..."
docker exec $CONTAINER bash -c \
"sed -i '/<remote>/,/<\/remote>/d' /var/ossec/etc/ossec.conf"


echo "[4] Adding correct Fortigate SYSLOG configuration..."

docker exec $CONTAINER bash -c "cat >> /var/ossec/etc/ossec.conf <<'CONFIG'

<remote>
  <connection>syslog</connection>
  <port>514</port>
  <protocol>udp</protocol>
  <allowed-ips>192.168.1.1</allowed-ips>
</remote>

CONFIG"


echo "[5] Creating Fortigate custom rule directory..."

docker exec $CONTAINER bash -c \
"mkdir -p /var/ossec/etc/rules"


echo "[6] Adding SOC detection rule..."

docker exec $CONTAINER bash -c "cat > /var/ossec/etc/rules/local_rules.xml <<'RULE'

<group name=\"fortigate,authentication_failed,\">

<rule id=\"100001\" level=\"10\">
 <if_sid>81606</if_sid>
 <description>
 Fortigate failed administrator login attempt detected
 </description>
 <mitre>
  <id>T1110</id>
 </mitre>
</rule>

</group>

RULE"


echo "[7] Testing configuration..."

docker exec $CONTAINER bash -c \
"/var/ossec/bin/wazuh-analysisd -t"


echo "[8] Restarting Wazuh..."

docker restart $CONTAINER


echo "[9] Waiting..."
sleep 15


echo "[10] Checking SYSLOG listener..."

docker logs $CONTAINER --tail 50 | grep "514"


echo "[11] Checking Fortigate alerts..."

docker exec $CONTAINER bash -c \
"tail -20 /var/ossec/logs/alerts/alerts.json"


echo "======================================"
echo "DONE"
echo "Fortigate -> Wazuh SOC pipeline fixed"
echo "======================================"

