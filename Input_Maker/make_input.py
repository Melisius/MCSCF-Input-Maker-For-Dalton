from Input_Maker import file_loader as fload
from Input_Maker import utility as util
from Input_Maker import analyser as anal
from Input_Maker import heuristics as heu

import numpy as np

class Input_Maker():
    # Bad naming: __type_wavefunction = wavefunction form output file
    #        and: wavefunction_type = wavefunction going into input file
    def __init__(self, output_file):
        """Get numbers from output file"""
        with open(output_file) as f:
            self.__load_file = list(f)
            
        self.__type_wavefunction = fload.wavefunction_type_output(self.__load_file)
        self.__orbitals_in_symmetries = fload.orbital_symmetries(self.__load_file)
        self.__number_symmetreis = len(self.__orbitals_in_symmetries)
        self.__total_nuclei_charge = fload.total_nuclei_charge(self.__load_file)
        
        if self.__type_wavefunction != "mp2": # Not MP2 wavefunction
            self.natural_occupations = fload.Natural_Occupations(self.__load_file, self.__number_symmetreis)
            self.__total_electrons = fload.electrons(self.__load_file)
        
        if self.__type_wavefunction == "mp2":
            self.number_closed_shell = fload.closed_shell_number(self.__load_file)
            self.Hartree_Fock_orbital_energies = fload.HF_orb_energies(self.__load_file, self.__number_symmetreis)
            self.__total_electrons = fload.electronsMP2(self.__load_file)
            self.natural_occupations = fload.Natural_Occupations_MP2(self.__load_file, self.__number_symmetreis)
            
        self.natural_occupation_sum = util.Natural_Occupation_Summation(self.natural_occupations)
        self.natural_occupations, self.natural_occupations_index = util.Sort_Natural_Occupations(self.natural_occupations)
        
        """Set variables for input files"""
        self.inactive = np.zeros(self.__number_symmetreis, dtype=int)
        self.CAS = np.zeros(self.__number_symmetreis, dtype=int)
        self.RAS1 = np.zeros(self.__number_symmetreis, dtype=int)
        self.RAS2 = np.zeros(self.__number_symmetreis, dtype=int)
        self.RAS3 = np.zeros(self.__number_symmetreis, dtype=int)
        self.RAS1_holes = np.array([0, 2], dtype=int)
        self.RAS3_electrons = np.array([0, 2], dtype=int)
        self.file_name = "input.dal"
        self.spin_multiplicity = 1
        self.MCSCF_method = "undefined"
        self.wavefunction_type = "MCSCF"
        self.symmetry = 1
        self.state = 1
        self.active_electrons = 0
        self.active_electrons_in_RAS2 = 0
        self.max_micro = 24
        self.max_macro = 24
        # MCSCFsrDFT stuff
        self.srxfunctional = "SRXPBEHSE"
        self.srcfunctional = "SRCPBERI"
        self.range_separation_parameter = 0.4
        
        """Some internal variables"""
        self.reorder_neglect_threshold = 0.001
        self.get_nat_occ_neglect_threshold = 0.001
        
        
    def pick_RAS_by_active_threshold(self, threshold):
        self.RAS1, self.RAS3, self.inactive = heu.Pick_RAS_active_threshold(threshold, self.natural_occupations)
        
        
    def pick_CAS_by_active_threshold(self, threshold):
        self.CAS, self.inactive = heu.Pick_CAS_active_threshold(threshold, self.natural_occupations)
        
        
    def scan_threshold_all(self):
        anal.threshold_scan_all(self.natural_occupations)
        
        
    def scan_threshold_per_sym(self):
        anal.threshold_scan_symmetries(self.natural_occupations)
    

    def get_natural_occupancies(self, threshold=1.9):
        anal.print_natural_occ(self.natural_occupations, threshold, self.get_nat_occ_neglect_threshold)
        
    def __write_active_space(self):
        self.__input_file.write("*CONFIGURATION INPUT"+"\n")
        self.__input_file.write(".INACTIVE"+"\n")
        self.__input_file.write(" ")
        for i in self.inactive:
            self.__input_file.write(str(i)+" ")
        self.__input_file.write("\n")
        
        if self.MCSCF_method == "cas":
            self.__input_file.write(".CAS SPACE"+"\n")
            self.__input_file.write(" ")
            for i in self.CAS:
                self.__input_file.write(str(i)+" ")
            self.__input_file.write("\n")
        elif self.MCSCF_method == "ras":
            self.__input_file.write(".RAS1 SPACE"+"\n")
            self.__input_file.write(" ")
            for i in self.RAS1:
                self.__input_file.write(str(i)+" ")
            self.__input_file.write("\n")
            
            self.__input_file.write(".RAS2 SPACE"+"\n")
            self.__input_file.write(" ")
            for i in self.RAS2:
                self.__input_file.write(str(i)+" ")
            self.__input_file.write("\n")
            
            self.__input_file.write(".RAS3 SPACE"+"\n")
            self.__input_file.write(" ")
            for i in self.RAS3:
                self.__input_file.write(str(i)+" ")
            self.__input_file.write("\n")
            
            self.__input_file.write(".RAS1 HOLES"+"\n")
            self.__input_file.write(" "+str(self.RAS1_holes[0])+" "+str(self.RAS1_holes[1])+"\n")
            self.__input_file.write(".RAS3 ELECTRONS"+"\n")
            self.__input_file.write(" "+str(self.RAS3_electrons[0])+" "+str(self.RAS3_electrons[1])+"\n")
        
        self.__input_file.write(".ELECTRONS"+"\n")
        self.__input_file.write(" "+str(self.active_electrons)+"\n")
        self.__input_file.write(".SYMMETRY"+"\n")
        self.__input_file.write(" "+str(self.symmetry)+"\n")
        
    def __write_reorder(self):
        symms = [[] for i in range(len(self.natural_occupations))]
        reorder = False
        counter = 0
        for key in self.natural_occupations:
            for i in range(0, len(self.natural_occupations_index[key])):
                if str(i) != str(self.natural_occupations_index[key][i]):
                    if self.natural_occupations[key][i] > self.reorder_neglect_threshold or self.natural_occupations[key][self.natural_occupations_index[key][i]] > self.reorder_neglect_threshold:
                        if self.natural_occupations[key][i] < 2 - self.reorder_neglect_threshold or self.natural_occupations[key][self.natural_occupations_index[key][i]] < 2 - self.reorder_neglect_threshold:
                            symms[counter].append(str(i+1)+" "+str(list(self.natural_occupations_index[key]).index(i)+1))
            counter += 1
        for i in range(len(symms)):
            if len(symms[i]) != 0:
                reorder = True
        
        if reorder == True:
            self.__input_file.write(".REORDER\n")
            for i in range(len(symms)):
                self.__input_file.write(str(len(symms[i]))+" ")
            self.__input_file.write("\n")
            for i in range(len(symms)):
                for j in range(len(symms[i])):
                    self.__input_file.write(str(symms[i][j])+" ")
            self.__input_file.write("\n")
    
    def write_input_file(self):
        """Check coherence in settings"""
        self.MCSCF_method = str(self.MCSCF_method).lower()
        self.wavefunction_type = str(self.wavefunction_type).lower()
        if self.MCSCF_method == "mcscfsrdft":
            self.MCSCF_method = "lrmcscf"
        
        if self.MCSCF_method == "cas":
            self.active_electrons = self.__total_electrons - np.sum(2*self.inactive, dtype=int) # number of active electrons must be this. Cannot infer number electrons just from CAS
        elif self.MCSCF_method == "ras":
            self.active_electrons = np.sum(2*self.RAS1, dtype=int) + self.active_electrons_in_RAS2 # Cannot infer from output file how many active electrons should be accounted for in RAS2
        else:
            assert False, "MCSCF_method is invalid, choose RAS or CAS"
        
        assert self.active_electrons ==  self.__total_electrons - np.sum(2*self.inactive, dtype=int), "Number of active electrons does not match active/inactive space"
        assert self.active_electrons%2 == 0, "Number of active electrons is uneven"
        assert self.__total_electrons%2 == 0, "Number of total electrons is uneven"
        
        """Print something useful"""
        print("Total molecular charge:", self.__total_nuclei_charge - self.__total_electrons)
        
        """Write input file"""
        self.__input_file = open(self.file_name, "w+")
        self.__input_file.write("**DALTON INPUT"+"\n")
        self.__input_file.write(".RUN WAVE FUNCTION"+"\n")
        self.__input_file.write("*MOLBAS\n")
        self.__input_file.write(".SYMTHR\n")
        self.__input_file.write(" 1.0D-4\n")
        
        """Write CI"""
        if self.wavefunction_type == "ci":
            self.__input_file.write("**WAVEFUNCTION"+"\n")
            self.__input_file.write(".CI\n")
            self.__input_file.write("*CI VECTOR"+"\n")
            self.__input_file.write(".PLUS COMBINATIONS"+"\n")
            self.__input_file.write("*CI INPUT"+"\n")
            self.__input_file.write(".CINO"+"\n")
            self.__input_file.write(".STATE"+"\n")
            self.__input_file.write(" "+str(self.state)+"\n")
            
            self.__write_active_space()
            
            self.__input_file.write("*ORBITAL INPUT"+"\n")
            self.__input_file.write(".MOSTART"+"\n")
            self.__input_file.write(" NEWORB"+"\n")
            
            self.__write_reorder()
            
            self.__input_file.write("*OPTIMIZATION"+"\n")
            self.__input_file.write(".DETERMI"+"\n")
            self.__input_file.write(".MAX MICRO ITERATIONS\n")
            self.__input_file.write(" "+str(self.max_micro)+"\n")
            self.__input_file.write(".MAX MACRO ITERATIONS\n")
            self.__input_file.write(" "+str(self.max_macro)+"\n")
            
        
        """Write MCSCF"""
        if self.wavefunction_type == "mcscf":
            self.__input_file.write("**WAVEFUNCTION"+"\n")
            self.__input_file.write(".MCSCF\n")
            
            self.__write_active_space()
            
            self.__input_file.write("*ORBITAL INPUT"+"\n")
            self.__input_file.write(".MOSTART"+"\n")
            self.__input_file.write(" NEWORB"+"\n")
            
            self.__write_reorder()
            
            self.__input_file.write("*OPTIMIZATION"+"\n")
            self.__input_file.write(".STATE"+"\n")
            self.__input_file.write(" "+str(self.state)+"\n")
            self.__input_file.write(".MAX MICRO ITERATIONS\n")
            self.__input_file.write(" "+str(self.max_micro)+"\n")
            self.__input_file.write(".MAX MACRO ITERATIONS\n")
            self.__input_file.write(" "+str(self.max_macro)+"\n")
        
        
        """Write lr-MCSCF"""
        if self.wavefunction_type == "lrmcscf":
            self.__input_file.write("**WAVEFUNCTION"+"\n")
            self.__input_file.write(".MCSRDFT\n")
            self.__input_file.write(".SRFUN\n")
            self.__input_file.write(" "+str(self.srxfunctional)+" "+str(self.srcfunctional)+"\n")
            
            self.__write_active_space()
            
            self.__input_file.write("*ORBITAL INPUT"+"\n")
            self.__input_file.write(".MOSTART"+"\n")
            self.__input_file.write(" NEWORB"+"\n")
            
            self.__write_reorder()
            
            self.__input_file.write("*OPTIMIZATION"+"\n")
            self.__input_file.write(".STATE"+"\n")
            self.__input_file.write(" "+str(self.state)+"\n")
            self.__input_file.write(".MAX MICRO ITERATIONS\n")
            self.__input_file.write(" "+str(self.max_micro)+"\n")
            self.__input_file.write(".MAX MACRO ITERATIONS\n")
            self.__input_file.write(" "+str(self.max_macro)+"\n")
            self.__input_file.write("**INTEGRALS\n")
            self.__input_file.write("*TWOINT\n")
            self.__input_file.write(".DOSRIN\n")
            self.__input_file.write(".ERF\n")
            self.__input_file.write(" "+str(self.range_separation_parameter)+"\n")
            
            
        self.__input_file.write("**END OF DALTON INPUT"+"\n")
        self.__input_file.close()
        
       