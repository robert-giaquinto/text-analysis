from __future__ import division, print_function, absolute_import
import os
import argparse
import logging

from src.utilities import unpickle_it
from src.topic_model.gensim_lda import GensimLDA
from src.topic_model.documents import Documents


def main():
    parser = argparse.ArgumentParser(description='Wrapper around the gensim LDA model.')
    parser.add_argument('-j', '--journal_file', type=str, help='Full path to the journal file to compute document topics probabilities on.')
    parser.add_argument('-d', '--data_dir', type=str, help='Directory of where to save or load bag-of-words, vocabulary, and model performance files.')
    parser.add_argument('-k', '--keep_n', type=int, help='How many terms (max) to keep in the dictionary file.')
    parser.add_argument('--num_test', type=int, default=0, help="Number of documents to hold out for the test set.")
    parser.add_argument('--num_docs', type=int, help="Number of documents in the journal file (specifying this can speed things up).")
    parser.add_argument('--num_topics', type=int, help="Number of topics in the model you want to use.")
    parser.add_argument('--n_workers', type=int, default=1, help="Number of cores to run on.")
    parser.add_argument('--log', dest="verbose", action="store_true", help='Add this flag to have progress printed to log.')
    parser.set_defaults(verbose=False)
    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logging.basicConfig(format='%(name)s : %(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    
    logger.info('extract_model_artifacts.py')
    print(args)

    lda_file = 'LDA_test_' + str(args.num_test) + '_train_' + str(args.num_docs - args.num_test) + '_topics_' + str(args.num_topics) + '.p'
    logger.info("Unpickling model:", lda_file)
    model = unpickle_it(os.path.join(args.data_dir, lda_file))
    model.topic_term_method = 'unweighted'
    model.topic_terms = model._unweighted_topic_terms()
    model.model.minimum_probability = 0.0
    
    logger.info("Saving word topic probabilities")
    model.save_word_topic_probs(os.path.join(args.data_dir, "unranked_word_topic_probs.txt"), metric="none")
    logger.info("Saving topic terms")
    model.save_topic_terms(os.path.join(args.data_dir, "unranked_unweighted_topic_terms.txt"), metric="none")

    logger.info("Initializing documents")
    docs = Documents(journal_file=args.journal_file,
                     num_test=args.num_test,
                     data_dir=args.data_dir,
                     rebuild=False,
                     keep_n=args.keep_n,
                     num_docs=args.num_docs,
                     verbose=args.verbose)
    
    # note: if num_test = 0, then the file for the documents keys will be wrong...
    if args.num_test == 0:
        docs.train_shard_file = args.journal_file
        docs.test_shard_file = None
    
    model._init_docs(docs)

    if args.n_workers == 1:
        logger.info("Saving document topics serially")
        model.save_doc_topic_probs(docs.train_bow, docs.train_keys, os.path.join(args.data_dir, "train_document_topic_probs.txt"))
        if args.num_test > 0:
            model.save_doc_topic_probs(docs.test_bow, docs.test_keys, os.path.join(args.data_dir, "test_document_topic_probs.txt"))
    else:
        logger.info("Saving document topics in parallel")
        model.n_workers = args.n_workers
        model.save_doc_topic_probs_parallel(docs.train_bow, docs.train_keys, os.path.join(args.data_dir, "train_document_topic_probs.txt"))
        if args.num_test > 0:
            model.save_doc_topic_probs_parallel(docs.test_bow, docs.test_keys, os.path.join(args.data_dir, "test_document_topic_probs.txt"))
        
    

if __name__ == '__main__':
    main()
