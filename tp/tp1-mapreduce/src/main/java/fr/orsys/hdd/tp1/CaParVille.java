package fr.orsys.hdd.tp1;

import java.io.IOException;

import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;

/**
 * Exercice « développer une tâche MapReduce » : chiffre d'affaires par ville.
 *
 *   yarn jar clients.jar fr.orsys.hdd.tp1.CaParVille /data/clean/clients/part-* /data/out/ca_villes
 *
 * Map    : (position, "id;nom;ville;ca;...") -> (ville, ca)
 * Reduce : (ville, [ca1, ca2, ...]) -> (ville, somme), également utilisé comme combiner.
 */
public class CaParVille extends Configured implements Tool {

  public static class CaMapper extends Mapper<LongWritable, Text, Text, DoubleWritable> {
    private final Text ville = new Text();
    private final DoubleWritable ca = new DoubleWritable();

    @Override
    protected void map(LongWritable off, Text ligne, Context ctx)
        throws IOException, InterruptedException {
      String[] f = ligne.toString().split(";");
      if (f.length < 4) {
        return;
      }
      try {
        ca.set(Double.parseDouble(f[3]));
      } catch (NumberFormatException e) {
        ctx.getCounter("CaParVille", "CA_ILLISIBLE").increment(1);
        return;
      }
      ville.set(f[2]);
      ctx.write(ville, ca);
    }
  }

  public static class SommeReducer extends Reducer<Text, DoubleWritable, Text, DoubleWritable> {
    private final DoubleWritable somme = new DoubleWritable();

    @Override
    protected void reduce(Text ville, Iterable<DoubleWritable> vals, Context ctx)
        throws IOException, InterruptedException {
      double total = 0;
      for (DoubleWritable v : vals) {
        total += v.get();
      }
      somme.set(Math.round(total * 100.0) / 100.0);
      ctx.write(ville, somme);
    }
  }

  @Override
  public int run(String[] args) throws Exception {
    if (args.length != 2) {
      System.err.println("Usage : CaParVille <entrée> <sortie>");
      return 2;
    }
    getConf().setIfUnset("mapreduce.output.textoutputformat.separator", ";");
    Job job = Job.getInstance(getConf(), "ca-par-ville");
    job.setJarByClass(CaParVille.class);
    job.setMapperClass(CaMapper.class);
    job.setCombinerClass(SommeReducer.class);
    job.setReducerClass(SommeReducer.class);
    job.setOutputKeyClass(Text.class);
    job.setOutputValueClass(DoubleWritable.class);
    FileInputFormat.addInputPath(job, new Path(args[0]));
    FileOutputFormat.setOutputPath(job, new Path(args[1]));
    boolean ok = job.waitForCompletion(true);
    Resultats.afficher(job);
    return ok ? 0 : 1;
  }

  public static void main(String[] args) throws Exception {
    System.exit(ToolRunner.run(new CaParVille(), args));
  }
}
