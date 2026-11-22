package fr.orsys.hdd.tp3;

import java.io.IOException;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.hbase.client.Admin;
import org.apache.hadoop.hbase.client.ColumnFamilyDescriptorBuilder;
import org.apache.hadoop.hbase.client.Connection;
import org.apache.hadoop.hbase.client.ConnectionFactory;
import org.apache.hadoop.hbase.client.TableDescriptor;
import org.apache.hadoop.hbase.client.TableDescriptorBuilder;

/**
 * Variante Java de la création de table (API à builders, HBase 2.x et 3.x) :
 * équivalent de  create 'catalogue', {NAME => 'info', VERSIONS => 3}, 'stock'
 *
 *   java -cp "$(hbase classpath):catalogue.jar" fr.orsys.hdd.tp3.CreerCatalogue
 */
public class CreerCatalogue {

  public static void main(String[] args) throws IOException {
    Configuration conf = HBaseConfiguration.create();
    try (Connection cnx = ConnectionFactory.createConnection(conf);
         Admin admin = cnx.getAdmin()) {
      if (admin.tableExists(Catalogue.TABLE)) {
        System.out.println("La table " + Catalogue.TABLE + " existe déjà : rien à faire.");
        return;
      }
      TableDescriptor td = TableDescriptorBuilder.newBuilder(Catalogue.TABLE)
          .setColumnFamily(ColumnFamilyDescriptorBuilder.newBuilder(Catalogue.INFO)
              .setMaxVersions(3).build())
          .setColumnFamily(ColumnFamilyDescriptorBuilder.of("stock"))
          .build();
      admin.createTable(td);
      System.out.println("Table " + Catalogue.TABLE + " créée.");
    }
  }
}
