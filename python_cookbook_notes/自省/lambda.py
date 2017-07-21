#!/usr/bin/python3
#coding:utf-8

#使用lambda函数
#Python 支持一种有趣的语法,它允许你快速定义单行的最小函数。这些叫做
#lambda 的函数,是从Lisp 借用来的,可以用在任何需要函数的地方

g = lambda x: x*2
print(g(3))

print((lambda x: x*2)(3))

'''
总的来说, lambda 函数可以接收任意多个参数 (包括可选参数) 并且返回单个
表达式的值。 lambda 函数不能包含命令,包含的表达式不能超过一个。不要
试图向 lambda 函数中塞入太多的东西;如果你需要更复杂的东西,应该定义
一个普通函数,然后想让它多长就多长
'''

#lambda 是可选的
'''
lambda 函数是一种风格问题。不一定非要使用它们;任何能够使用它们的地
方,都可以定义一个单独的普通函数来进行替换。我将它们用在需要封装特
殊的、非重用代码上,避免令我的代码充斥着大量单行函数
'''

'''
apihelper.py中的 lambda 函数:
    processFunc = collapse and (lambda s: " ".join(s.split())) or (lambda s: s)
    
    注意这里使用了 and-or 技巧的简单形式,它是没问题的,因为 lambda 函数在
布尔环境中总是为真。(这并不意味这 lambda 函数不能返回假值。这个函数对
象的布尔值为真;它的返回值可以是任何东西。)
还要注意的是使用了没有参数的 split 函数。你已经看到过它带一个或者两个
参数的使用,但是不带参数它按空白进行分割
'''