import pyspark as ps

# vdb checker helpers

# ConfigHandler object to handle potential sanity check fails
# Arguments ups, cs, and rws will be [False] if their sanity checks are not passed.


class configHandler:
    def __init__(
        self, usepool_status=True, cacheStatus=True, rwStatus=True, authMode=True
    ) -> None:
        self.ups = usepool_status
        self.cs = cacheStatus
        self.rws = rwStatus
        self.am = authMode

    # builds a message that contains sanity check result. Returns empty string if passes check.
    def get_msg(self) -> str:
        content_to_send = []
        if not self.ups:
            content_to_send.append(
                'Connection Pooling is turned off. ("usepool": false) in config.'
            )
        if not self.cs:
            content_to_send.append(
                'Caching is disabled. ("cacheEnabled": false) in config.'
            )
        if not self.rws:
            content_to_send.append(
                "Read/write split is disabled. Check configuration file rule section."
            )
        if not self.am:
            content_to_send.append(
                "Authentication mode (authMode) is not set to 'passthrough', username and password need to be separately configured in the vdb."
            )
        return "\n".join(content_to_send)


# function to perform basic sanity checks on a configuration file
def sanity_check(conf: ps.sql.DataFrame) -> configHandler:
    # check usepool
    usepool_status = conf.select("sources").collect()[0]["sources"][0]["usepool"]
    # chceck cache
    cacheStatus = conf.select("vdbs").collect()[0]["vdbs"][0]["cacheEnabled"]
    # check for proper r/w rules
    rw_rules = conf.select("rules").collect()[0]["rules"][0]["rules"]
    rwStatus = False
    for rule in rw_rules:
        if "(?i)^select" in rule["patterns"]:
            rwStatus = True
            break
    # check whether authMode is passthrough
    authMode = conf.select("vdbs").collect()[0]["vdbs"][0]["authMode"] == "passthrough"
    return configHandler(usepool_status, cacheStatus, rwStatus, authMode)


#############################################################################################

# Log analysis helpers


# function to standardize log column names (header names). e.g. no dahses, no unnecessary info
def fix_header(log: ps.sql.DataFrame) -> ps.sql.DataFrame:
    log = log.withColumnRenamed(log.columns[0], log.columns[0].split(" ")[1])
    columns = log.columns
    for col in columns:
        log = log.withColumnRenamed(col, col.replace("-", "_"))

    return log
