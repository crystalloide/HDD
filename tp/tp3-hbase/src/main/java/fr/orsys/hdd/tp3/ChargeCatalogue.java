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
 * Chargement initial du catalogue par lots de Put.
 *
 *   java -cp "$(hbase classpath):catalogue.jar" fr.orsys.hdd.tp3.ChargeCatalogue produits.csv [taille_lot]
 *
 * Fichier : id;libelle;categorie;prix;quantite;entrepot (avec en-tête).
 * Toutes les cellules reçoivent l'horodatage du 2026-01-01 (création du catalogue) :
 * les changements de prix datés, appliqués ensuite, deviennent ainsi des versions
 * plus récentes de la même cellule.
 */
public class ChargeCatalogue {

  static final String DATE_CREATION = "2026-01-01";

  public static void main(String[] args) throws IOException {
    if (args.length < 1) {
      System.err.println("Usage : ChargeCatalogue <produits.csv> [taille_lot]");
      System.exit(2);
    }
    int tailleLot = args.length > 1 ? Integer.parseInt(args[1]) : 50;
    long ts = Catalogue.horodatage(DATE_CREATION);
    Configuration conf = HBaseConfiguration.create();
    int total = 0;
    int lots = 0;
    try (Connection cnx = ConnectionFactory.createConnection(conf);
         Table table = cnx.getTable(Catalogue.TABLE);
         BufferedReader in = Files.newBufferedReader(Paths.get(args[0]), StandardCharsets.UTF_8)) {
      List<Put> lot = new ArrayList<>();
      String ligne = in.readLine();                       // en-tête
      while ((ligne = in.readLine()) != null) {
        String[] f = ligne.split(";", -1);
        if (f.length != 6) {
          System.err.println("ligne ignorée : " + ligne);
          continue;
        }
        Put p = new Put(Bytes.toBytes(f[0]));
        p.addColumn(Catalogue.INFO, Bytes.toBytes("libelle"), ts, Bytes.toBytes(f[1]));
        p.addColumn(Catalogue.INFO, Bytes.toBytes("categorie"), ts, Bytes.toBytes(f[2]));
        p.addColumn(Catalogue.INFO, Catalogue.PRIX, ts, Bytes.toBytes(f[3]));
        p.addColumn(Catalogue.STOCK, Bytes.toBytes("quantite"), ts, Bytes.toBytes(f[4]));
        p.addColumn(Catalogue.STOCK, Bytes.toBytes("entrepot"), ts, Bytes.toBytes(f[5]));
        lot.add(p);
        if (lot.size() == tailleLot) {
          table.put(lot);                                 // un seul aller-retour par lot
          total += lot.size();
          lots++;
          lot.clear();
        }
      }
      if (!lot.isEmpty()) {
        table.put(lot);
        total += lot.size();
        lots++;
      }
    }
    System.out.printf("CHARGEMENT produits=%d lots=%d%n", total, lots);
  }
}
