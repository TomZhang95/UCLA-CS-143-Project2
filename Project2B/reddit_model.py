from __future__ import print_function
from pyspark import SparkConf, SparkContext
from pyspark.sql import SQLContext
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType
from pyspark.sql.types import BooleanType
from pyspark.ml.feature import CountVectorizer
import bz2file
import os
import cleantext
import pandas

# IMPORT OTHER MODULES HERE

def main(context):
    """Main function takes a Spark SQL context."""
    # YOUR CODE HERE
    # YOU MAY ADD OTHER FUNCTIONS AS NEEDED


    # TASK 1: Load the comments (BZ2 JSON), submissions (BZ2 JSON) and labeled
    # data (CSV) into PySpark.
    labeled_data_pd = pandas.DataFrame(pandas.read_csv("labeled_data.csv"))
    labeled_data_df = context.createDataFrame(labeled_data_pd)

    submissions_df = context.read.json("submissions.json.bz2")
    submissions_df.printSchema()

    comments_minimal_df = context.read.json("comments-minimal.json.bz2")
    comments_minimal_df.printSchema()
    comments_minimal_df = comments_minimal_df.select('id','body','created_utc','link_id','author_flair_text')


    # TASK 2: To train a classifier, we only need to work with the labeled data,
    # but labeled_data.csv ONLY contains a comment_id, and 3 sentiment labels.
    # The comments file contains the actual comments and a bunch of other information.
    # We need to do something with these two data frames so we only have data associated
    # with the labeled data.
    joined_df = labeled_data_df.join(comments_minimal_df, labeled_data_df.Input_id==comments_minimal_df.id)
    joined_df.repartition(1).write.format("com.databricks.spark.csv").option("header", "true").save("joined")


    # TASK 4: Generate the unigrams, bigrams and trigrams for each comment in the labeled
    # data and store all of them combined into one column.
    # TASK 5: To train a model, we must have all features in one column, as an array of
    # strings. Combine the unigrams, bigrams, trigrams and participating subreddits into
    # the same column.
    parse_udf = udf(cleantext.sanitize, StringType())
    joined_df = joined_df.withColumn("parsed", parse_udf(joined_df.body))



    # TASK 6A: Use a binary CountVectorizer to turn the raw features into a sparse feature
    # vector, a data structure that Spark ML understands.
    cv = CountVectorizer(inputCol="parsed", outputCol="features", minDF=5.0)
    model = cv.fit(joined_df)
    result = model.transform(joined_df)
    result.show()


    # TASK 6B: Create two new columns representing the positive and negative labels.
    # Take the original labels {1, 0, -1, -99} and do the following. Construct a column
    # for the positive label that is 1 when the original label is 1, and 0 everywhere else.
    # Construct a column for the negative label that is 1 when the original label is -1
    # and 0 everywhere else.

    pos_udf = udf(construct_positive(), BooleanType())
    neg_udf = udf(construct_negative(), BooleanType())
    result.withColumn("positive", pos_udf(joined_df.labeldjt))
    result.withColumn("negative", neg_udf(joined_df.labeldjt))


def construct_positive(i):
    """
    Return true if i == 1
    :param i: int
    :return: boolean
    """
    if i == 1:
        return True
    else:
        return False

def construct_negative(i):
    """
    Return true if i == -1
    :param i: int
    :return: boolean
    """
    if i == -1:
        return True
    else:
        return False



if __name__ == "__main__":
    os.environ['PYSPARK_PYTHON'] = '/usr/local/bin/python3'
    conf = SparkConf().setAppName("CS143 Project 2B")
    conf = conf.setMaster("local[*]")
    sc   = SparkContext(conf=conf)
    sqlContext = SQLContext(sc)
    sc.addPyFile("cleantext.py")
    main(sqlContext)
