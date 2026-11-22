package fr.orsys.hdd.tp1;

import java.io.IOException;

import org.apache.hadoop.mapreduce.Counters;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.TaskCounter;

/** Affiche l'identifiant du job et les compteurs utiles aux TP (lignes greppables). */
final class Resultats {

  private Resultats() { }

  static void afficher(Job job) throws IOException, InterruptedException {
    System.out.println("HDD_JOB_ID=" + job.getJobID());
    System.out.println("HDD_ETAT=" + job.getJobState());
    Counters c = job.getCounters();
    if (c == null) {
      return;
    }
    System.out.printf("HDD_COMPTEURS map_in=%d map_out=%d combine_in=%d combine_out=%d reduce_in=%d reduce_out=%d%n",
        c.findCounter(TaskCounter.MAP_INPUT_RECORDS).getValue(),
        c.findCounter(TaskCounter.MAP_OUTPUT_RECORDS).getValue(),
        c.findCounter(TaskCounter.COMBINE_INPUT_RECORDS).getValue(),
        c.findCounter(TaskCounter.COMBINE_OUTPUT_RECORDS).getValue(),
        c.findCounter(TaskCounter.REDUCE_INPUT_RECORDS).getValue(),
        c.findCounter(TaskCounter.REDUCE_OUTPUT_RECORDS).getValue());
  }
}
