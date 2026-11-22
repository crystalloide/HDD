package fr.orsys.hdd.tp4;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

/**
 * Client Java JDBC : interroge le référentiel par HiveServer2... ou par Impala,
 * avec le même pilote (protocole HiveServer2) et la même requête.
 *
 *   java -cp "$HIVE_JDBC:referentiel-pig.jar" fr.orsys.hdd.tp4.ReferentielJdbc \
 *        "jdbc:hive2://hiveserver2:10000/default" hive
 *   java -cp "$HIVE_JDBC:referentiel-pig.jar" fr.orsys.hdd.tp4.ReferentielJdbc \
 *        "jdbc:hive2://impalad:21050/default;auth=noSasl" impala
 */
public class ReferentielJdbc {

  static final String REQUETE =
      "SELECT ville, COUNT(*) AS nb_clients, ROUND(SUM(ca_total), 2) AS ca_total "
      + "FROM referentiel.clients_orc GROUP BY ville ORDER BY ca_total DESC LIMIT 10";

  public static void main(String[] args) throws SQLException, ClassNotFoundException {
    String url = args.length > 0 ? args[0] : "jdbc:hive2://hiveserver2:10000/default";
    String utilisateur = args.length > 1 ? args[1] : "hive";
    Class.forName("org.apache.hive.jdbc.HiveDriver");
    long debut = System.nanoTime();
    try (Connection cnx = DriverManager.getConnection(url, utilisateur, "");
         Statement st = cnx.createStatement();
         ResultSet rs = st.executeQuery(REQUETE)) {
      System.out.printf("%-22s %10s %16s%n", "ville", "clients", "ca_total");
      while (rs.next()) {
        System.out.printf("%-22s %10d %16.2f%n", rs.getString(1), rs.getLong(2), rs.getDouble(3));
      }
    }
    System.out.printf("JDBC_DUREE_MS=%d (%s)%n", (System.nanoTime() - debut) / 1_000_000, url);
  }
}
