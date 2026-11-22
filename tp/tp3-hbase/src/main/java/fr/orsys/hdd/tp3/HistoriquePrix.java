package fr.orsys.hdd.tp3;

import java.io.IOException;
import java.time.Instant;
import java.time.ZoneOffset;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.Cell;
import org.apache.hadoop.hbase.CellUtil;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.hbase.client.Connection;
import org.apache.hadoop.hbase.client.ConnectionFactory;
import org.apache.hadoop.hbase.client.Get;
import org.apache.hadoop.hbase.client.Result;
import org.apache.hadoop.hbase.client.Table;
import org.apache.hadoop.hbase.util.Bytes;

/**
 * Historique d'un prix : les N dernières versions de la cellule info:prix.
 *
 *   java -cp "$(hbase classpath):catalogue.jar" fr.orsys.hdd.tp3.HistoriquePrix P0001 [3]
 */
public class HistoriquePrix {

  public static void main(String[] args) throws IOException {
    if (args.length < 1) {
      System.err.println("Usage : HistoriquePrix <id_produit> [nb_versions]");
      System.exit(2);
    }
    int versions = args.length > 1 ? Integer.parseInt(args[1]) : 3;
    Configuration conf = HBaseConfiguration.create();
    try (Connection cnx = ConnectionFactory.createConnection(conf);
         Table table = cnx.getTable(Catalogue.TABLE)) {
      Get get = new Get(Bytes.toBytes(args[0]));
      get.addColumn(Catalogue.INFO, Catalogue.PRIX);
      get.readVersions(versions);
      Result r = table.get(get);
      if (r.isEmpty()) {
        System.out.println("Produit inconnu : " + args[0]);
        return;
      }
      System.out.println("Versions de info:prix pour " + args[0] + " (la plus récente en premier) :");
      for (Cell c : r.getColumnCells(Catalogue.INFO, Catalogue.PRIX)) {
        System.out.printf("  %s  %s%n",
            Instant.ofEpochMilli(c.getTimestamp()).atZone(ZoneOffset.UTC).toLocalDate(),
            Bytes.toString(CellUtil.cloneValue(c)));
      }
    }
  }
}
