#ifndef CANDIDATE_LIST_H
#define CANDIDATE_LIST_H

namespace Ime {

class CandidateList {
public:
	CandidateList(void);
	virtual ~CandidateList(void);

	int totalPage();
	int choicePerPage();
	int totalChoice();
	int currentPage();
	int hasNext();
	char candidateString();
};

}

#endif
