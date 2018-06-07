from __future__ import print_function
from pyspark import SparkConf, SparkContext
from pyspark.sql import SQLContext
import pandas as pd
import cleantext
from pyspark.sql.types import *
from pyspark.sql.functions import col, split
from pyspark.ml.feature import CountVectorizer
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml.evaluation import BinaryClassificationEvaluator
import re
# IMPORT OTHER MODULES HERE

def main(context):
    """Main function takes a Spark SQL context."""
    # YOUR CODE HERE
    # YOU MAY ADD OTHER FUNCTIONS AS NEEDED
    #comments = sqlContext.read.json("comments-minimal.json.bz2")
    #submissions = sqlContext.read.json("submissions.json.bz2")

    #################task_1#######################################
    '''''
    # write parquet file
    comments = context.read.json("./data/comments-minimal.json.bz2")

    # Displays the content of the DataFrame to stdout
    comments.show()

    comments.write.parquet("./www/comments.parquet")

    submissions = context.read.json("./data/submissions.json.bz2")

    # Displays the content of the DataFrame to stdout
    submissions.show()

    submissions.write.parquet("./www/submissions.parquet")
    '''''
    # to read parquet file
    comments = context.read.parquet("./www/comments.parquet")
    #comments.printSchema()
    #comments.show()
    submissions = context.read.parquet("./www/submissions.parquet")

    # to read labeled data
    labeled_pd = pd.DataFrame(pd.read_csv("./www/labeled_data.csv"))
    labeled = context.createDataFrame(labeled_pd)
    #labeled = context.read.csv('./www/labeled_data.csv')
    ################################################################

    ################task_2#########################################
    comments.createOrReplaceTempView("comments_view")
    labeled.createOrReplaceTempView("labeled_view")
    comments_labeled = context.sql('SELECT  comments_view.id AS comments_id, labeled_view.Input_id, body, labeldem, labelgop, labeldjt  FROM comments_view JOIN labeled_view ON comments_view.id = labeled_view.Input_id')
    #rows = comments_labeled.count
    #print(rows)
    ###############################################################

    ###############task_4 & task_5##########################################
    def list_to_string(list):
        list = list[1:]
        L = " ".join(str(x) for x in list)
        return L

    comments_labeled.createOrReplaceTempView("comments_labeled")
    context.udf.register("sanitize", cleantext.sanitize)
    context.udf.register("list_to_string", list_to_string)
    comments_labeled_data = context.sql('SELECT comments_id, Input_id, list_to_string(sanitize(body)) AS body,labeldem, labelgop, labeldjt FROM comments_labeled')
    comments_labeled_data = comments_labeled_data.withColumn("body", split(col("body"), " ").cast(ArrayType(StringType())))
    #comments_labeled_data.select("body").show()
    ###############################################################

    ################task_6A###########################################

    cv = CountVectorizer(inputCol="body", outputCol="features", minDF=5.0)
    model = cv.fit(comments_labeled_data)
    #comments_data = model.transform(comments_labeled_data)#.select("features").show(truncate=False)

    ####################################################################
    '''''
    ################task_6B###############################################
    comments_data.createOrReplaceTempView("comments_data_view")
    #comments_data.show()
    comments_data_pos = context.sql("SELECT comments_id, Input_id, features, IFNULL(IF(labeldjt = 1, 1, NULL), 0) AS label FROM comments_data_view")
    comments_data_neg = context.sql( "SELECT comments_id, Input_id, features, IFNULL(IF(labeldjt = -1, 1, NULL), 0) AS label FROM comments_data_view")

    #comments_data.show()

    ######################################################################

    ##################task_7################################################
    # Initialize two logistic regression models.
    # Replace labelCol with the column containing the label, and featuresCol with the column containing the features.
    poslr = LogisticRegression(labelCol="label", featuresCol="features", maxIter=10)
    neglr = LogisticRegression(labelCol="label", featuresCol="features", maxIter=10)
    # This is a binary classifier so we need an evaluator that knows how to deal with binary classifiers.
    posEvaluator = BinaryClassificationEvaluator()
    negEvaluator = BinaryClassificationEvaluator()
    # There are a few parameters associated with logistic regression. We do not know what they are a priori.
    # We do a grid search to find the best parameters. We can replace [1.0] with a list of values to try.
    # We will assume the parameter is 1.0. Grid search takes forever.
    posParamGrid = ParamGridBuilder().addGrid(poslr.regParam, [1.0]).build()
    negParamGrid = ParamGridBuilder().addGrid(neglr.regParam, [1.0]).build()
    # We initialize a 5 fold cross-validation pipeline.
    posCrossval = CrossValidator(
        estimator=poslr,
        evaluator=posEvaluator,
        estimatorParamMaps=posParamGrid,
        numFolds=5)
    negCrossval = CrossValidator(
        estimator=neglr,
        evaluator=negEvaluator,
        estimatorParamMaps=negParamGrid,
        numFolds=5)
    # Although crossvalidation creates its own train/test sets for
    # tuning, we still need a labeled test set, because it is not
    # accessible from the crossvalidator (argh!)
    # Split the data 50/50
    posTrain, posTest = comments_data_pos.randomSplit([0.8, 0.2])
    negTrain, negTest = comments_data_neg.randomSplit([0.8, 0.2])
    # Train the models
    #print("Training positive classifier...")
    #posModel = posCrossval.fit(posTrain)
    print("Training negative classifier...")
    negModel = negCrossval.fit(negTrain)

    # Once we train the models, we don't want to do it again. We can save the models and load them again later.
    #posModel.save("www/pos.model")
    negModel.save("www/neg.model")

    ########################################################################
    '''''
    ####################task_8###############################################

    def remove(string):
        if(string.find('/s') == -1):
            return True
        elif(string.find('&gt') != 0):
            return True
        else:
            return False

    def link_id(id):
        id = re.sub('t3_', '', id)
        return id

    def list_to_string(list):
        list = list[1:]
        L = " ".join(str(x) for x in list)
        return L

    comments.createOrReplaceTempView("comments_view")
    submissions.createOrReplaceTempView("submissions_view")
    comments_sorted = context.sql("SELECT id, link_id, body, created_utc, author_flair_text, score FROM comments_view ORDER BY link_id")
    comments_sorted.createOrReplaceTempView("comments_sorted_view")
    #comments_sorted.show()
    submissions_sorted = context.sql("SELECT id, title, score FROM submissions_view ORDER BY id")
    submissions_sorted.createOrReplaceTempView("submissions_sorted_view")
    #submissions_sorted.show()
    context.udf.register("remove", remove)
    context.udf.register("link_id", link_id)
    context.udf.register("sanitize", cleantext.sanitize)
    context.udf.register("list_to_string", list_to_string)
    comments_unseen = context.sql("SELECT comments_sorted_view.id, submissions_sorted_view.id AS link_id, list_to_string(sanitize(body)) AS body, created_utc, author_flair_text, title,  comments_sorted_view.score AS comments_score, submissions_sorted_view.score AS story_score FROM comments_sorted_view JOIN submissions_sorted_view ON link_id(comments_sorted_view.link_id) == submissions_sorted_view.id AND remove(comments_sorted_view.body)== TRUE")
    #comments_unseen.show()
    comments_unseen_data = comments_unseen.withColumn("body", split(col("body"), " ").cast(ArrayType(StringType())))
    #comments_unseen_data.show()

    comments_unseen_data = model.transform(comments_unseen_data)#.select("features").show(truncate=False)
    #comments_unseen_data.show()
    comments_unseen_data.write.parquet("./www/comments_unseen.parquet")

    '''''
    print("Writing comments_unseen_data.csv")
    tmp = comments_unseen_data.toPandas()
    tmp.to_csv("./www/comments_unseen_data.csv", index=False, sep=' ')
    '''''
    # print("Reading Vectorized.csv")
    # tmp = pd.DataFrame(pd.read_csv("./www/vectorized.csv", sep=' '))
    # comments_data = context.createDataFrame(tmp)






    ###########################################################################





















if __name__ == "__main__":
    sc.stop()

    conf = SparkConf().setAppName("CS143 Project 2B")
    conf = conf.setMaster("local[*]")
    sc   = SparkContext(conf=conf)
    sqlContext = SQLContext(sc)
    sc.addPyFile("./www/cleantext.py")
    '''''
    spark = SparkSession \
        .builder \
        .master('local[*]')\
        .appName("CS143 Project 2B") \
        .config('spark.executor.memory', '5gb') \
        .config("spark.cores.max", "6") \
        .getOrCreate()
    sc = spark.sparkContext
    sc.addPyFile("./www/cleantext.py")
    # using SQLContext to read parquet file

    sqlContext = SQLContext(sc)
    '''''
    main(sqlContext)
