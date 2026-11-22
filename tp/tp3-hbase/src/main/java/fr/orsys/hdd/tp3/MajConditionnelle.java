package fr.orsys.hdd.tp3;

import java.io.IOException;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.hbase.client.CheckAndMutate;
import org.apache.hadoop.hbase.client.CheckAndMutateResult;
import org.apache.hadoop.hbase.client.Connection;
import org.apache.hadoop.hbase.client.ConnectionFactory;
import org.apache.hadoop.hbase.client.Put;
import org.apache.hadoop.hbase.client.Table;
import org.apache.hadoop.hbase.util.Bytes;

/**
 * Mise à jour conditionnelle (« compare-and-set ») : le nouveau prix n'est
 * écrit que si le prix courant vaut toujours la valeur attendue. Test et
 * écriture sont atomiques sur le RegionServer.
 *
 *   java -cp "$(hbase classpath):catalogue.jar" fr.orsys.hdd.tp3.MajConditionnelle P0001 27.90 25.90
 */
public class MajConditionnelle {

  public static void main(String[] args) throws IOException {
    if (args.length != 3) {
      System.err.println("Usage : MajConditionnelle <id_produit> <prix_attendu> <nouveau_prix>");
      System.exit(2);
    }
    byte[] ligne = Bytes.toBytes(args[0]);
    Configuration conf = HBaseConfiguration.create();
    try (Connection cnx = ConnectionFactory.createConnection(conf);
         Table table = cnx.getTable(Catalogue.TABLE)) {
      Put put = new Put(ligne).addColumn(Catalogue.INFO, Catalogue.PRIX, Bytes.toBytes(args[2]));
      CheckAndMutate cam = CheckAndMutate.newBuilder(ligne)
          .ifEquals(Catalogue.INFO, Catalogue.PRIX, Bytes.toBytes(args[1]))
          .build(put);
      CheckAndMutateResult res = table.checkAndMutate(cam);
      if (res.isSuccess()) {
        System.out.printf("MAJ_OK %s : %s -> %s%n", args[0], args[1], args[2]);
      } else {
        System.out.printf("MAJ_REFUSEE %s : le prix courant n'est plus %s%n", args[0], args[1]);
      }
    }
  }
}
