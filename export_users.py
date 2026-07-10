import csv
import time
import logging


def get_users(gis):
    return gis.users.search()


def inspect_users(users):
    for user in users:
        name = user.get("fullName")
        email = user.get("email")
        username = user.username
        usertype = map_role_to_usertype(user.role)
        role = user.role  # raw role value from the portal

        logging.info(
            f"User: {username}, Full Name: {name}, Email: {email}, Type: {usertype}, Role: {role}"
        )


def map_role_to_usertype(role: str) -> str:
    match role:
        case "org_admin":
            return "Creator"
        case "org_publisher":
            return "Creator"
        case "org_user":
            return "Viewer"

        case "Viewer":
            return "Viewer"
        case "Data Editor":
            return "Creator"
        case "Publisher":
            return "Creator"

        case _:
            return "Viewer"


def export_to_csv(users, out):
    with open(out, "w") as output:
        dataWriter = csv.writer(
            output,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\n",
        )
        # Write header row.
        dataWriter.writerow(
            ["Full Name", "Email", "Username", "Date Created", "Type", "Role"]
        )

        for user in users:
            name = user.get("fullName")
            role = user.role
            usertype = map_role_to_usertype(role)
            logging.debug(f"Recording {name} in role {role}.")
            if user.role == "org_admin":
                userRole = "Administrator"
            elif user.role == "org_publisher":
                userRole = "Publisher"
            elif user.role == "org_user":
                userRole = "User"
            else:
                userRole = user.role
            dataWriter.writerow(
                [
                    user.get("fullName"),
                    user.get("email"),
                    user.username,
                    time.strftime("%Y-%m-%d", time.gmtime(user["created"] / 1000)),
                    usertype,
                    userRole,
                ]
            )


def export_users(gis, out):
    users = get_users(gis)
    logging.info("Total Portal Users: " + str(len(users)))
    export_to_csv(users, out)
    logging.info(f"Table exported to {out}.")


if __name__ == "__main__":
    gis = GIS_CONN
