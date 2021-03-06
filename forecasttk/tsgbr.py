__author__ = "Christoph Schauer"
__date__ = "2019-11-13"


import numpy
from pandas import Series, DataFrame, period_range
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error
from matplotlib import pyplot


class SeasonalGBRX(GradientBoostingRegressor):
    """
    Child class of sklearn.ensemble.GradientBoostingRegressor, inheriting everything from this 
    class. Extends this class with several attributes and methods for easy-to-use modeling and 
    forecasting of time series with gradient boosting regression models. 
    Requires as input and returns as output pandas series with PeriodIndex. 
    """

    def __init__(
        self, y, frequencies, exog=None,
        loss="ls", learning_rate=0.1, n_estimators=100, subsample=1.0, criterion="friedman_mse", 
        min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_depth=3, 
        min_impurity_decrease=0.0, min_impurity_split=None, init=None, random_state=None, 
        max_features=None, alpha=0.9, verbose=0, max_leaf_nodes=None, warm_start=False, 
        presort="auto", validation_fraction=0.1, n_iter_no_change=None, tol=0.0001
        ):
        super().__init__(
            loss, learning_rate, n_estimators, subsample, criterion, min_samples_split, 
            min_samples_leaf, min_weight_fraction_leaf, max_depth, min_impurity_decrease, 
            min_impurity_split, init, random_state, max_features, alpha, verbose, max_leaf_nodes, 
            warm_start, presort, validation_fraction, n_iter_no_change, tol
            )

        self.y = y
        self.frequencies = frequencies
        self.X_exog = None
        self.X_endog = None
        self.error_list = None


    def gen_X_endog(self, index, frequencies):
        """
        Generates a dataframe with time sequences for each frequency in 'frequencies' as input for 
        the 'fit_ts' method.
        """
        X_endog = DataFrame(index=index)
        X_endog["date"] = X_endog.index   
        
        if "year" in frequencies:
            X_endog["year"] = X_endog["date"].dt.year
        if "quarter" in frequencies:
            X_endog["quarter"] = X_endog["date"].dt.quarter
        if "month" in frequencies:
            X_endog["month"] = X_endog["date"].dt.month    
        if "weekofyear" in frequencies:
            X_endog["weekofyear"] = X_endog["date"].dt.weekofyear
        if "dayofyear" in frequencies:
            X_endog["dayofyear"] = X_endog["date"].dt.dayofyear
        if "dayofmonth" in frequencies:
            X_endog["dayofmonth"] = X_endog["date"].dt.day
        if "dayofweek" in frequencies:
            X_endog["dayofweek"] = X_endog["date"].dt.dayofweek  
            
        return X_endog[frequencies]


    def fit_ts(self):
        """
        Fits a gradient boosting regression model with features generated by the 'gen_X_endog' 
        method to 'self.y'.
        """
        self.X_endog = self.gen_X_endog(index=self.y.index, frequencies=self.frequencies)
        self.fit(self.X_endog, self.y)
        return self


    def fit_ts_with_staged_predict(self, y_test, n_estimators):
        """
        Fits a gradient boosting regression model with features generated by the 'gen_X_endog' 
        method to 'self.y' using staged prediction with 'n_estimators'. Stores the model with 
        the lowest RMSE in a test set 'y_test'
        """

        self.n_estimators = n_estimators
        self.X_endog = self.gen_X_endog(index=self.y.index, frequencies=self.frequencies)
        X_endog_test = self.gen_X_endog(index=y_test.index, frequencies=self.frequencies)

        # Staged prediction
        self.fit(self.X_endog, self.y)
        self.error_list = [(mean_squared_error(y_test, y_pred))**0.5 for y_pred in self.staged_predict(X_endog_test)]
        
        # Overwrite n_estimators with best n_estimators and fit model again
        self.n_estimators = numpy.argmin(self.error_list)
        self.fit(self.X_endog, self.y)

        return self


    def plot_n_estimators(self):    
        """
        Plots RMSE over all 'n_estimators' used in the 'fit_ts_with_staged_predict' method.
        """
        pyplot.figure(figsize=(10, 5))
        pyplot.plot(self.error_list)
        pyplot.xlim(0, len(self.error_list))
        pyplot.xlabel("n_estimators")
        pyplot.ylabel("RMSE")
        pyplot.show()



    def predict_ts(self):
        """
        Predicts values for 'self.y'. with the fitted model.
        """
        y_pred = self.predict(self.X_endog)
        return Series(y_pred, index=self.y.index)


    def forecast_ts(self, steps):
        """
        Forecasts values for 'steps' steps after the last period in 'self.y.index'
        """
        idx_fcst = period_range(self.y.index[-1] + 1, periods=steps)
        X_endog = self.gen_X_endog(index=idx_fcst, frequencies=self.frequencies)
        y_fcst = self.predict(X_endog)
        return Series(y_fcst, index=idx_fcst)


