db.auth("vds", "2022")
db = db.getSiblingDB("videtics")

db.createUser(
    {
        user: "vds_data_sync",
        pwd: "data_sync_password",
        roles: [{role: "readWrite", db: "videtics"}]
    }
)

db.createUser(
    {
        user: "vds_data_control",
        pwd: "data_control_password",
        roles: [{role: "readWrite", db: "videtics"}]
    }
)

db.createUser(
    {
        user: "vds_data_versioning",
        pwd: "data_versioning_password",
        roles: [{role: "readWrite", db: "videtics"}]
    }
)