package fr.orsys.hdd.tp3;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.hbase.client.Connection;
import org.apache.hadoop.hbase.client.ConnectionFactory;
import org.apache.hadoop.hbase.client.Put;
import org.apache.hadoop.hbase.client.Table;
import org.apache.hadoop.hbase.util.Bytes;

/**
 * Application des modifications datées du catalogue.
 *
 *   java -cp "$(hbase classpath):catalogue.jar" fr.orsys.hdd.tp3.AppliqueModifications modifications.csv
 *
 * Fichier : id;famille;colonne;valeur;date_effet (avec en-tête).
 * Chaque Put porte l'horodatage de sa date d'effet : HBase conserve alors une
 * nouvelle version de la cellule (3 au maximum dans la famille info).
 */
public class AppliqueModifications {

  public static void main(String[] args) throws IOException {
    if (args.length != 1) {
      System.err.println("Usage : AppliqueModifications <modifications.csv>");
      System.exit(2);
    }
    Configuration conf = HBaseConfiguration.create();
    List<Put> puts = new ArrayList<>();
    try (BufferedReader in = Files.newBufferedReader(Paths.get(args[0]), StandardCharsets.UTF_8)) {
      String ligne = in.readLine();                       // en-tête
      while ((ligne = in.readLine()) != null) {
        String[] f = ligne.split(";", -1);
        if (f.length != 5) {
          continue;
        }
        Put p = new Put(Bytes.toBytes(f[0]));
        p.addColumn(Bytes.toBytes(f[1]), Bytes.toBytes(f[2]), Catalogue.horodatage(f[4]),
            Bytes.toBytes(f[3]));
        puts.add(p);
      }
    }
    try (Connection cnx = ConnectionFactory.createConnection(conf);
         Table table = cnx.getTable(Catalogue.TABLE)) {
      table.put(puts);
    }
    System.out.printf("MODIFICATIONS appliquees=%d%n", puts.size());
  }
}
