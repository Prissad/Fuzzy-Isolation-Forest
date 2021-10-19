from collections import OrderedDict
import matplotlib.pyplot as plt
import seaborn as sns
import skfuzzy as fuzz
import numpy as np
from skfuzzy import control as ctrl
import pandas as pd

def interpolate(x, mf, xx):
  df = pd.DataFrame({'x': x, 'mf':mf})
  df = df.sort_values(by='x')
  return fuzz.interp_membership(df.x,df.mf,xx)

class Fuzzifier():
  """
  Fuzzifier class: given a DataFrame of Crisp Data Return corresponding fuzzified data
  ----------
  Parameters
  ----------
  x : dataframe-like
      Universe variables. Contains the features data (must be numerical)
      Required.
  modalities : Dictionnary where every key corresponds to a feature
      and values are either an object containing the modalities as keys, and the membership function (or 'auto') as value,
      or auto as key and the number of modalities as value . Optional.
      exemple: {'age': {'old': {'trimf': [0,1,2]}, 'young': {'gaussmf': [0,1]}}}
      exemple2: {'age': {'auto' : 3}}
  Methods
  -------
  """
  def __init__(self, x, modalities = {}):
    self.x = x
    self.modalities = modalities
    self.variables = OrderedDict()
    self.df = pd.DataFrame()


  def __getitem__(self, key):
        """
        Calling `fuzzifier['label']` will return the 'label' fuzzy variable
        """
        if key in self.variables.keys():
            return self.variables[key]
        else:
            # Build a pretty list of available fuzzy variables and raise an
            # informative error message
            options = '['
            for available_key in self.variables.keys():
              options += "'" + str(available_key) + "',"
            options += ']'
            raise ValueError("Fuzzy Variable {0}' does not exist.\n "
                             "Available options: {1}".format(key, options))
            

  
  def fuzzify(self):
    """
    The fuzzifying procedure, takes no params.
    """
    # TODO: verify params passed and raise errors if any problem

    for variable_name in self.x.columns:
      # Create the FuzzyVariable object
      fuzzyVar = ctrl.Antecedent(self.x[variable_name], variable_name)
      
      # check if key is present in modalities, if it is create modalities else auto
      if variable_name in self.modalities.keys():
        self.__fuzzify_numerical_in_modalities(variable_name,fuzzyVar)
       

      else:
        # If variable name neither categorical nor present in the passed object
        fuzzyVar.automf(3)

      self.variables[variable_name] = fuzzyVar

    # If the fuzzy method is recalled, recreate the DataFrame on toDataFrame method call
    self.df = pd.DataFrame()


  def __fuzzify_numerical_in_modalities(self, variable_name,fuzzyVar):

     # Get modalities corresponding to that feature name
      modalities = self.modalities[variable_name]

      # check if the modalities object is {'auto': 3/5/7} create the memberships automatically 
      if (next(iter(modalities)) == 'auto'):
        # Get number of triangular membership function (3, 5 or 7)
        n = modalities['auto']

        # Auto Generate membership functions
        fuzzyVar.automf(n);

      else :
        # For each modality (like 'old' or 'young') add the membership function to the fuzzy var
        for modality in modalities.items():

          # Assign membership values to fuzzy var
          # modality[0] is the modality name, modality[1] is the membership + values dict
          fuzzyVar[modality[0]] = self.__getMembership(fuzzyVar.universe, modality[1])

  # Utility method returning the sci-kit fuzzy membership function given the name of the membership function
  def __getMembership(self,x, membershipFunctionData):

    # Get the membership function type; can be trimf, gaussmf or trapmf or auto
    membership_name = next(iter(membershipFunctionData))

    if (membership_name == 'trimf' ):
      return fuzz.trimf(x, membershipFunctionData[membership_name])

    if (membership_name == 'trapmf' ):
      return fuzz.trapmf(x, membershipFunctionData[membership_name])

    if (membership_name == 'gaussmf'):
      return fuzz.gaussmf(x, membershipFunctionData[membership_name][0],membershipFunctionData[membership_name][1] )
    return None

  # After fuzzification, use this method to return a DataFrame containing the fuzzified Data
  def toDataFrame(self):

    # Only Generate the dictionnary once
    if (not self.df.empty):
      return self.df

    self.df = pd.DataFrame({}, index = self.x.index)

    for fuzzyVar_name, fuzzy_var in self.variables.items():
      # create columns and append to DataFrame
      for modality in fuzzy_var.terms:
        self.df['{0};{1}'.format(fuzzyVar_name, modality)] = fuzzy_var[modality].mf
    return self.df

  def interpolate_new_entry(self, xx):
    new_df = pd.DataFrame({}, index = [0])
    for fuzzyVar_name, fuzzy_var in self.variables.items():
      # create columns and append to DataFrame
      for modality in fuzzy_var.terms:
        new_df['{0};{1}'.format(fuzzyVar_name, modality)] = interpolate(self.x.loc[:,fuzzyVar_name],fuzzy_var[modality].mf, xx.loc[:,fuzzyVar_name])
    return new_df
  

  def view(self):
    """
    Show the membership functions to each variable
    """
    for fuzzyVar_name, fuzzy_var in self.variables.items():
      fig, ax = plt.subplots()
      labels = []

      for modality in fuzzy_var.terms:
        labels.append(modality)
        sns.lineplot(ax = ax, x = fuzzy_var.universe, y = fuzzy_var[modality].mf)
      
      ax.legend(labels = labels)
      plt.title(fuzzyVar_name)
      plt.show()
