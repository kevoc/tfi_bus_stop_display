#!/bin/bash

#
# This bash script will take 3 files for TLS auth and bundle them
# into 1, in the format expected by the MQTTController() class in
# this project. The format for the bundled file is very simple,
# just comments denoting the different certs/keys.
#
# use this file as follows, replacing the paths to your cert files
# as required.
#
#   tools/create_cert_bundle.sh  ~/ca.crt  ~/admin.crt  ~/admin.key  src_uC/client.crt
#
#        $1 = the CA certificate
#        $2 = the client certificate, signed by the CA in arg $1
#        $3 = the client private key
#        $4 = the target bundle file to be created after the first 3 args are validated
#

usage() { echo "Usage:   $0  CA_cert  client_cert  key_file  bundle_out" 1>&2; exit 1; }
[ $# -ne 4 ] && usage

ca=$1
client_cert=$2
client_key=$3
bundle_out=$4

echo "Certificate Authority: $ca";
echo "Private Key:           $client_key";
echo "Client Cert:           $client_cert";
echo "Bundle Output:         $bundle_out";


# first, make sure the client cert was signed by the CA
echo ""
echo " * Checking Client Certificate was signed by the CA..."
openssl verify -CAfile "$ca" "$client_cert"

if [ $? -ne 0 ]; then
  echo "ERROR: client cert invalid for this CA"
  exit 1;
fi


echo ""
echo " * Checking Client Certificate and Private Key match..."
ClientCertModulus=`openssl x509 -noout -modulus -in "$client_cert"`
ClientKeyModulus=`openssl rsa -noout -modulus -in "$client_key"`

# echo "Client Certificate Modulus:"
# echo $ClientCertModulus

# echo "Private Key Modulus:"
# echo $PrivateKeyModulus


if [ "$ClientCertModulus" != "$ClientKeyModulus" ]; then
  echo "ERROR: client cert and client key do not match"
  exit 1;
else
  echo "Success!"
fi


function is_key_type() {
  openssl "$1" -in "$2" -text -noout >/dev/null 2>/dev/null
  is_pem_format=$?

  openssl "$1" -in "$2" -inform der -text -noout >/dev/null 2>/dev/null
  is_der_format=$?

  if [ $is_pem_format -eq 0 -o $is_der_format -eq 0 ]; then
    return 0
  else
    return 1
  fi
}

function is_certificate() {
  is_key_type "x509" "$1"
}

function is_private_key () {
  is_key_type "rsa" "$1"
}


function is_der_format() {
  openssl x509 -in "$1" -inform der -text -noout >/dev/null 2>/dev/null
  is_der_cert=$?

  openssl rsa -in "$1" -inform der -text -noout >/dev/null 2>/dev/null
  is_der_key=$?

  if [ $is_der_cert -eq 0 -o $is_der_key -eq 0 ]; then
    return 0
  else
    return 1
  fi
}


echo ""
echo " * Verifying certificates are in DER format..."
for file in "$ca" "$client_cert" "$client_key"; do
  if ! is_der_format "$file"; then
    echo "ERROR: $file is not in DER format, it will be converted before bundling..."
  fi
done


function file_size_bytes () {
  wc -c "$1" | awk '{print $1}'
}


function bundle_as_der () {
  # convert the file to der if it's not already
  #  $1 = the bundled name
  #  $2 = the path to the file

  if is_der_format "$2"; then
    FILE_PATH="$2"
  else
    #temp_file=`mktemp`
    temp_file="/tmp/`basename "$2"`"
    if is_certificate "$2"; then
      openssl x509 -in $2 -out "$temp_file" -outform DER
    elif is_private_key "$2"; then
      openssl rsa -in $2 -out "$temp_file" -outform DER
    else
      echo "ERROR: unrecognised file $2"
      exit 1
    fi
    FILE_PATH="$temp_file"
  fi

  echo "##### $1 `file_size_bytes "$FILE_PATH"` #####" >>"$3"
  cat "$FILE_PATH" >>"$3"
}

echo ""
echo " * Bundling all files in DER format..."

# delete the old file
if [ -e "$bundle_out" ]; then rm "$bundle_out"; fi
#
## bundle all files together
#cat > "$bundle_out" << EOF
#$(bundle_as_der  ca           "$ca")
#$(bundle_as_der  client_cert  "$client_cert")
#$(bundle_as_der  client_key   "$client_key")
#EOF

bundle_as_der  ca           "$ca"            "$bundle_out"
bundle_as_der  client_cert  "$client_cert"   "$bundle_out"
bundle_as_der  client_key   "$client_key"    "$bundle_out"
