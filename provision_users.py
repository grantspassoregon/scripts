import csv
import json
import logging
import requests


def provision_users_from_csv(gis, csv_path):
    # Build list of users to send to Portaladmin
    users_payload = {"users": []}

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fullname = row["Full Name"]
            email = row["Email"]
            username = row["Username"]
            role = row["Role"]  # Viewer, Editor, Creator, etc.
            usertype = row[
                "Type"
            ]  # UserType from your CSV (Viewer, Creator, GISProfessionalAdvanced)

            logging.info(f"Preparing {username} ({role}, {usertype})")

            users_payload["users"].append(
                {
                    "username": username,
                    "fullname": fullname,
                    "email": email,
                    "provider": "enterprise",
                    "idpUsername": username,  # SAML identity
                    "role": role,
                    "userType": usertype,
                }
            )

    # Prepare Portaladmin endpoint request
    admin_url = gis.url + "/portaladmin/security/users/createOrUpdateUsers"
    token = gis._con.token

    logging.info("Sending user list to Portaladmin for pre-provisioning...")

    resp = requests.post(
        admin_url,
        data={"f": "json", "token": token, "users": json.dumps(users_payload)},
        verify=False,
    )

    logging.info("Portaladmin response:")
    logging.info(resp.text)

    return resp.json()


if __name__ == "__main__":
    # GIS_CONN must already be defined from your login flow
    gis = GIS_CONN

    csv_path = r"C:\temp\final_users.csv"
    provision_users_from_csv(gis, csv_path)
