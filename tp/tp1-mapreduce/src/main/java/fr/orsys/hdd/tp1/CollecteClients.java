package fr.orsys.hdd.tp1;

import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Counters;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.mapreduce.lib.output.MultipleOutputs;
import org.apache.hadoop.mapreduce.lib.output.TextOutputFormat;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;

/**
 * Driver du job de collecte (map seul).
 *
 *   yarn jar clients.jar fr.orsys.hdd.tp1.CollecteClients /data/raw/clients /data/clean/clients
 *
 * Résultat : part-m-* (lignes valides) et rejets-m-* (lignes écartées, avec leur motif).
 */
public class CollecteClients extends Configured implements Tool {

  static final String SORTIE_REJETS = "rejets";

  @Override
  public int run(String[] args) throws Exception {
    if (args.length != 2) {
      System.err.println("Usage : CollecteClients <entrée> <sortie>");
      return 2;
    }
    Job job = Job.getInstance(getConf(), "collecte-clients");
    job.setJarByClass(CollecteClients.class);
    job.setMapperClass(CollecteMapper.class);
    job.setNumReduceTasks(0);                         // job « map seul »
    job.setOutputKeyClass(NullWritable.class);
    job.setOutputValueClass(Text.class);
    MultipleOutputs.addNamedOutput(job, SORTIE_REJETS, TextOutputFormat.class,
        NullWritable.class, Text.class);
    FileInputFormat.addInputPath(job, new Path(args[0]));
    FileOutputFormat.setOutputPath(job, new Path(args[1]));

    boolean ok = job.waitForCompletion(true);
    Resultats.afficher(job);
    Counters c = job.getCounters();
    if (c == null) {
      return ok ? 0 : 1;
    }
    System.out.printf("COLLECTE lues=%d valides=%d entetes=%d rejets=%d%n",
        c.findCounter(CollecteMapper.Collecte.LIGNES_LUES).getValue(),
        c.findCounter(CollecteMapper.Collecte.LIGNES_VALIDES).getValue(),
        c.findCounter(CollecteMapper.Collecte.ENTETES).getValue(),
        c.findCounter(CollecteMapper.Collecte.REJETS).getValue());
    return ok ? 0 : 1;
  }

  public static void main(String[] args) throws Exception {
    System.exit(ToolRunner.run(new CollecteClients(), args));
  }
}
