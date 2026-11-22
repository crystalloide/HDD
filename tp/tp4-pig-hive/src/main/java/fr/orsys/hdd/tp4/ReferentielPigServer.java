package fr.orsys.hdd.tp4;

import java.io.IOException;
import java.util.Iterator;

import org.apache.pig.ExecType;
import org.apache.pig.PigServer;
import org.apache.pig.backend.executionengine.ExecJob;
import org.apache.pig.data.Tuple;

/**
 * Java pilote Pig (Pig embarqué) : l'application enchaîne des instructions
 * Pig Latin, que PigServer compile en jobs MapReduce soumis à YARN.
 *
 *   HADOOP_CLASSPATH="$PIG_JAR:$PIG_HOME/lib/*" \
 *     hadoop jar referentiel-pig.jar fr.orsys.hdd.tp4.ReferentielPigServer \
 *       /data/referentiel/clients/raffinee/clients /data/referentiel/clients/raffinee/segments
 *
 * Calcul : pour les clients présents dans plusieurs canaux, nombre de clients
 * et CA moyen par segment.
 */
public class ReferentielPigServer {

  public static void main(String[] args) throws IOException {
    if (args.length != 2) {
      System.err.println("Usage : ReferentielPigServer <référentiel> <sortie>");
      System.exit(2);
    }
    String entree = args[0];
    String sortie = args[1];
    PigServer pig = new PigServer(ExecType.MAPREDUCE);
    try {
      if (pig.existsFile(sortie)) {
        pig.deleteFile(sortie);
      }
      pig.registerQuery("ref = LOAD '" + entree + "' USING PigStorage(';') AS ("
          + "id:chararray, nom:chararray, ville:chararray, segment:chararray, ca_total:double, "
          + "nb_canaux:long, canaux:chararray, date_premiere_inscription:chararray);");
      pig.registerQuery("multi = FILTER ref BY nb_canaux > 1;");
      pig.registerQuery("par_segment = GROUP multi BY segment;");
      pig.registerQuery("stats = FOREACH par_segment GENERATE group AS segment, "
          + "COUNT(multi) AS nb_clients, ROUND_TO(AVG(multi.ca_total), 2) AS ca_moyen;");
      ExecJob job = pig.store("stats", sortie, "PigStorage(';')");
      System.out.println("PIG_STATUT=" + job.getStatus());
      Iterator<Tuple> resultats = job.getResults();
      while (resultats.hasNext()) {
        System.out.println("  " + resultats.next());
      }
    } finally {
      pig.shutdown();
    }
  }
}
