package fr.orsys.hdd.tp1;

import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;

/**
 * Driver : nombre de clients par ville.
 *
 *   yarn jar clients.jar fr.orsys.hdd.tp1.ClientsParVille [options -D] <entrée> <sortie>
 *
 * Options (-D, lues grâce à ToolRunner) :
 *   hdd.combiner=true            active le combiner (= ClientsReducer)
 *   mapreduce.job.reduces=2      nombre de reducers (1 par défaut)
 *   mapreduce.job.queuename=dev  file YARN (TP YARN)
 *   hdd.map.pause.ms=3000        pause au démarrage de chaque map (TP YARN)
 */
public class ClientsParVille extends Configured implements Tool {

  @Override
  public int run(String[] args) throws Exception {
    if (args.length != 2) {
      System.err.println("Usage : ClientsParVille [-D propriété=valeur ...] <entrée> <sortie>");
      return 2;
    }
    getConf().setIfUnset("mapreduce.output.textoutputformat.separator", ";");
    Job job = Job.getInstance(getConf(), "clients-par-ville");
    job.setJarByClass(ClientsParVille.class);
    job.setMapperClass(ClientsMapper.class);
    if (getConf().getBoolean("hdd.combiner", false)) {
      job.setCombinerClass(ClientsReducer.class);
    }
    job.setReducerClass(ClientsReducer.class);
    job.setOutputKeyClass(Text.class);
    job.setOutputValueClass(IntWritable.class);
    // Le nombre de reducers vient de mapreduce.job.reduces (-D) : pas de valeur
    // codée en dur ici, pour pouvoir comparer 1 et 2 reducers sans recompiler.
    FileInputFormat.addInputPath(job, new Path(args[0]));
    FileOutputFormat.setOutputPath(job, new Path(args[1]));

    boolean ok = job.waitForCompletion(true);
    Resultats.afficher(job);
    return ok ? 0 : 1;
  }

  public static void main(String[] args) throws Exception {
    System.exit(ToolRunner.run(new ClientsParVille(), args));
  }
}
