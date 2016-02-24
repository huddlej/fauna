import os, json, datetime
import rethinkdb as r
from Bio import SeqIO

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-db', '--database', default='vdb', help="database to download from")
parser.add_argument('-v', '--virus', default='Zika', help="virus table to interact with")
parser.add_argument('--path', default='data/', help="path to dump output files to")
parser.add_argument('--ftype', default='fasta', help="output file format, default \"fasta\", other is \"json\"")
parser.add_argument('--fname', default=None, help="default output file name is \"VirusName_Year-Month-Date\"")

class vdb_download(object):

    def __init__(self, database, virus, ftype, path='data/'):

        '''
        parser for virus, fasta fields, output file names, output file format path, interval
        '''

        self.database = database
        self.virus_type = virus
        self.output_file_type = 'json'

        self.path = path
        self.current_date = str(datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d'))


        self.viruses = []

        # connect to database
        try:
            r.connect(host="ec2-52-90-204-136.compute-1.amazonaws.com", port=28015, db=self.database, auth_key="KeHiybPoX8BM6aAhfYqy").repl()
            print("Connected to the \"" + self.database + "\" database")
        except:
            print("Failed to connect to the database, " + self.database)
            raise Exception

    def download_all_documents(self):
        '''
        download all documents from table
        :return:
        '''

        cursor = list(r.db(self.database).table(self.virus_type).run())
        for doc in cursor:
            self.pick_best_sequence(doc)
        self.viruses = cursor
        print("Downloading all viruses from the table: " + self.virus_type)

    def pick_best_sequence(self, document):
        '''
        find the best sequence in the given document. Currently by longest sequence.
        Resulting document is with flatter dictionary structure
        '''
        list_sequences = document['sequences']
        if len(list_sequences) == 1:
            best_sequence_info = document['sequences'][0]
        else:
            longest_sequence_pos = 0
            longest_sequence_length = len(document['sequences'][0]['sequence'])
            current_pos = 0
            for sequence_info in document['sequences']:
                if len(sequence_info['sequence']) > longest_sequence_length or (len(sequence_info['sequence']) ==
                                                        longest_sequence_length and sequence_info['accession'] is None):
                    longest_sequence_length = len(sequence_info['sequence'])
                    longest_sequence_pos = current_pos
                current_pos += 1
            best_sequence_info = document['sequences'][longest_sequence_pos]

        # create flatter structure for virus info
        for atr in best_sequence_info.keys():
            document[atr] = best_sequence_info[atr]
        del document['sequences']


    def write_json(self, data, fname, indent=1):
        '''
        writes as list of viruses (dictionaries)
        '''
        fname += ".json"
        try:
            handle = open(fname, 'w')
        except:
            print("Couldn't open output file")
            print(fname)
            raise FileNotFoundError
        else:
            json.dump(data, handle, indent=indent)
            handle.close()
            print("Wrote to " + fname)

    def write_fasta(self, viruses, fname):
        fasta_fields = ['strain', 'virus', 'accession', 'date', 'region', 'country', 'division', 'location', 'source', 'locus']
        fname += ".fasta"
        try:
            handle = open(fname, 'w')
        except IOError:
            pass
        else:
            for v in viruses:
                handle.write(">")
                for field in fasta_fields:
                    if v[field] is None:
                        v[field] = '?'
                    handle.write(str(v[field]) + "|")
                handle.write("\n")
                handle.write(v['sequence'] + "\n")
            handle.close()
            print("Wrote to " + fname)

    def output(self, file_type, fname):
        if fname is None:
            fname = self.path + self.virus_type + "/" + self.virus_type + "_" + self.current_date
        else:
            fname = self.path + self.virus_type + "/" + fname
        if file_type == 'json':
            self.write_json(self.viruses, fname)
        else:
            self.write_fasta(self.viruses, fname)

if __name__=="__main__":

    args = parser.parse_args()
    run = vdb_download(args.database, args.virus, args.ftype)
    run.download_all_documents()
    run.output(args.ftype, args.fname)