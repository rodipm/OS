class Memory:
    def __init__(self):
        self.size = 1000 # bytes
        self.segment_size = 10
        self.number_segments = self.size // self.segment_size
        self.segments = [None for _ in range(self.number_segments)]
        self.free_segments = self.number_segments

    def __str__(self):
        str_rep = str()
        for i, segment in enumerate(self.segments):
            if i % 10 == 0 and i != 0:
                str_rep += "\n"
            seg_rep = str(segment) if segment != None else 'x'
            str_rep += str(seg_rep) + " "
        return str_rep
    
    def allocate(self, job_id, job_size):
        requested_number_segments = job_size//self.segment_size
        requested_number_segments += 1 if job_size % self.segment_size else 0


        if requested_number_segments > self.free_segments:
            return False
        
        allocated_segments = []
        for i in range(len(self.segments)):
            if self.segments[i] == None:
                self.segments[i] = job_id 
                allocated_segments.append(i)
                self.free_segments -= 1

                if len(allocated_segments) == requested_number_segments:
                    break

        return allocated_segments

    def deallocate(self, job_id):
        has_job = False
        for i, seg in enumerate(self.segments[:]):
            if seg == job_id:
                if not has_job:
                    has_job == True
                self.segments[i] = None
                self.free_segments += 1
        return has_job
