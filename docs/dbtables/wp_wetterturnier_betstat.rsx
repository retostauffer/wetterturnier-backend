
.. csv-table:: [Autogenerated table scheme of table "wp_wetterturnier_betstat] Wetterturnier Wordpress Plugin forecast stats table. Does contain the overall points (not points for single forecasted parameters)."
    :header: "Field", "Type", "Null", "Key", "Default", "Extra"

    "userID","int(11)","NO","PRI","None",""
    "cityID","smallint(5) unsigned","NO","PRI","None",""
    "tdate","smallint(6)","NO","PRI","None",""
    "points_d1","float","YES","","None",""
    "points_d2","float","YES","","None",""
    "points","float","YES","","None",""
    "rank","smallint(5) unsigned","YES","","None",""
    "updated","timestamp","NO","","CURRENT_TIMESTAMP","on update CURRENT_TIMESTAMP"
    "submitted","timestamp","YES","","None",""


